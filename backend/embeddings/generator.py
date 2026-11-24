"""Generates embeddings using Google Gemini API.

Uses the google.genai package. Includes timeout, bounded retry with backoff+jitter
for transient network failures, and clear error classification.
"""

import logging
import os
import random
import time
from typing import List, Optional

import google.genai as genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
import httpx

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings using Google Gemini API."""

    MAX_RETRIES = 5
    BASE_BACKOFF_SECONDS = 1.0
    MAX_BACKOFF_SECONDS = 30.0
    # google.genai HttpOptions.timeout is in milliseconds.
    REQUEST_TIMEOUT_MS = int(os.getenv("GEMINI_TIMEOUT_MS", "60000"))
    CONNECT_TIMEOUT_SECONDS = float(os.getenv("GEMINI_CONNECT_TIMEOUT_SECONDS", "10"))
    READ_TIMEOUT_SECONDS = float(os.getenv("GEMINI_READ_TIMEOUT_SECONDS", "60"))
    WRITE_TIMEOUT_SECONDS = float(os.getenv("GEMINI_WRITE_TIMEOUT_SECONDS", "10"))
    POOL_TIMEOUT_SECONDS = float(os.getenv("GEMINI_POOL_TIMEOUT_SECONDS", "10"))

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set. "
                "Obtain your API key from: https://aistudio.google.com/"
            )

        self.embedding_model = (
            model or os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
        ).strip()
        self.dimension = int(os.getenv("GEMINI_EMBEDDING_DIMENSION", "3072"))
        self._client = self._build_client()

    def _build_client(self) -> genai.Client:
        timeout = httpx.Timeout(
            timeout=self.READ_TIMEOUT_SECONDS,
            connect=self.CONNECT_TIMEOUT_SECONDS,
            read=self.READ_TIMEOUT_SECONDS,
            write=self.WRITE_TIMEOUT_SECONDS,
            pool=self.POOL_TIMEOUT_SECONDS,
        )
        http_options = genai_types.HttpOptions(
            timeout=self.REQUEST_TIMEOUT_MS,
            client_args={"timeout": timeout},
        )
        return genai.Client(api_key=self.api_key, http_options=http_options)

    def close(self) -> None:
        """Best-effort close of underlying HTTP client if exposed by SDK."""
        try:
            api_client = getattr(self._client, "_api_client", None)
            httpx_client = getattr(api_client, "_httpx_client", None) if api_client else None
            if httpx_client and hasattr(httpx_client, "close"):
                httpx_client.close()
        except Exception:
            logger.debug("Failed to close Gemini HTTP client", exc_info=True)

    @staticmethod
    def _sanitize_error(exc: Exception) -> str:
        msg = str(exc).strip().replace("\n", " ")
        msg = " ".join(msg.split())
        return msg[:300] if msg else exc.__class__.__name__

    def _is_permanent_error(self, exc: Exception) -> bool:
        if isinstance(exc, (ValueError, TypeError)):
            return True
        if isinstance(exc, genai_errors.ClientError):
            status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
            if status in {400, 401, 403, 404, 422}:
                return True
            text = str(exc).lower()
            if any(k in text for k in ["api key", "permission", "unauthorized", "not found", "invalid argument", "unsupported"]):
                return True
            # 429/resource exhausted is transient/rate-limited.
            if status == 429 or "resource_exhausted" in text or "rate" in text:
                return False
            return False
        return False

    def _is_transient_error(self, exc: Exception) -> bool:
        if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError, httpx.TransportError)):
            return True
        if isinstance(exc, genai_errors.ServerError):
            return True
        if isinstance(exc, genai_errors.ClientError):
            status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
            text = str(exc).lower()
            if status == 429:
                return True
            if "resource_exhausted" in text or "rate" in text or "too many requests" in text:
                return True
            return False
        # Fallback for wrapped transport errors from SDK
        text = str(exc).lower()
        transient_markers = [
            "timeout", "timed out", "temporarily unavailable", "connection reset",
            "connection aborted", "connection refused", "name or service not known",
            "dns", "ssl", "handshake", "503", "502", "504",
        ]
        return any(m in text for m in transient_markers)

    def _compute_backoff(self, attempt: int) -> float:
        base = min(self.MAX_BACKOFF_SECONDS, self.BASE_BACKOFF_SECONDS * (2 ** attempt))
        # jitter in [50%, 100%] of base
        return base * (0.5 + random.random() * 0.5)

    def _execute_with_retry(self, func, operation: str):
        last_exception: Optional[Exception] = None
        for attempt in range(self.MAX_RETRIES):
            try:
                return func()
            except Exception as exc:  # noqa: BLE001 - classify then rethrow/raise sanitized
                last_exception = exc
                if self._is_permanent_error(exc) or not self._is_transient_error(exc):
                    raise

                if attempt >= self.MAX_RETRIES - 1:
                    break

                delay = self._compute_backoff(attempt)
                logger.warning(
                    "Transient Gemini %s failure (attempt %s/%s, retry_in=%.2fs): %s",
                    operation,
                    attempt + 1,
                    self.MAX_RETRIES,
                    delay,
                    self._sanitize_error(exc),
                )
                time.sleep(delay)

        assert last_exception is not None
        raise RuntimeError(
            f"Gemini {operation} failed after {self.MAX_RETRIES} attempts: "
            f"{self._sanitize_error(last_exception)}"
        ) from last_exception

    def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for the given text using Gemini."""
        if not text or not text.strip():
            raise ValueError("Text parameter must not be empty")

        def _call_api():
            config = genai_types.EmbedContentConfig(
                output_dimensionality=self.dimension,
                task_type="RETRIEVAL_DOCUMENT",
            )
            try:
                result = self._client.models.embed_content(
                    model=self.embedding_model,
                    contents=text,
                    config=config,
                )
            except Exception:
                # Fallback for models/configs that reject output_dimensionality
                result = self._client.models.embed_content(
                    model=self.embedding_model,
                    contents=text,
                )
            embedding = self._extract_embedding(result)
            if not embedding:
                raise RuntimeError("Embedding API returned no embedding.")
            if len(embedding) != self.dimension:
                raise RuntimeError(
                    f"Unexpected embedding dimension: {len(embedding)}, expected {self.dimension}"
                )
            return list(embedding)

        return self._execute_with_retry(_call_api, operation="embedding")

    @staticmethod
    def _extract_embedding(result) -> Optional[List[float]]:
        if isinstance(result, dict):
            emb_list = result.get("embeddings") or []
            if emb_list and isinstance(emb_list[0], dict):
                return emb_list[0].get("values") or []
            return None
        emb_list = getattr(result, "embeddings", None) or []
        if not emb_list:
            return None
        first = emb_list[0]
        values = getattr(first, "values", None)
        if values is None and isinstance(first, dict):
            values = first.get("values")
        return list(values) if values is not None else None

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts sequentially (rate-limit safe)."""
        if not texts:
            return []
        for text in texts:
            if not text or not text.strip():
                raise ValueError("Text parameter must not be empty")
        return [self.generate_embedding(text) for text in texts]
