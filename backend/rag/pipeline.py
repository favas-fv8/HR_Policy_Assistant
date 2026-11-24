import os
import logging
import random
import time
from typing import List, Dict, Tuple

import fitz  # PyMuPDF
from django.conf import settings

from embeddings.generator import EmbeddingGenerator
from vector.similarity import retrieve_top_chunks
from rag.chunking import PageText, chunk_pages, get_chunking_config, normalize_text

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline for HR Policy Assistant.
    """

    def __init__(self):
        self.embedding_generator = EmbeddingGenerator(
            api_key=settings.GEMINI_API_KEY
        )
        self.similarity_threshold = float(
            os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7")
        )
        self.retrieval_limit = int(os.getenv("RAG_RETRIEVAL_LIMIT", "5"))
        cfg = get_chunking_config()
        self.chunk_target_tokens = cfg["target_tokens"]
        self.chunk_max_tokens = cfg["max_tokens"]
        self.chunk_overlap_tokens = cfg["overlap_tokens"]
        self.chunk_min_tokens = cfg["min_tokens"]
        # Legacy fields retained for API/status compatibility
        self.chunk_size = self.chunk_target_tokens
        self.chunk_overlap = self.chunk_overlap_tokens
        self.gen_model = os.getenv("GEMINI_GENERATION_MODEL", "gemini-3-flash-preview")
        self.gen_fallback_models = [
            m.strip()
            for m in os.getenv(
                "GEMINI_GENERATION_FALLBACK_MODELS",
                "gemini-flash-latest,gemini-2.5-flash",
            ).split(",")
            if m.strip()
        ]
        self.gen_max_retries = int(os.getenv("GEMINI_GENERATION_MAX_RETRIES", "4"))
        self.use_pgvector = self._check_pgvector_availability()

    def close(self) -> None:
        try:
            self.embedding_generator.close()
        except Exception:
            logger.debug("Failed to close embedding generator", exc_info=True)
    
    def _check_pgvector_availability(self) -> bool:
        """
        Check if pgvector extension is available in the database.
        Tries to import/ping the extension.
        Returns True if pgvector is available, False otherwise.
        """
        try:
            import django
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                # Test that vector operations work
                cursor.execute("SELECT 1::vector <=> '[1,0,0]'::vector")
                return True
        except Exception:
            return False
    
    def extract_pages(self, pdf_file_path: str) -> Tuple[List[str], int]:
        """Extract text per page from PDF using PyMuPDF."""
        try:
            doc = fitz.open(pdf_file_path)
            pages = [doc[page_num].get_text("text") for page_num in range(len(doc))]
            page_count = len(doc)
            doc.close()
            return pages, page_count
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF: {e}")

    def extract_text_from_pdf(self, pdf_file_path: str) -> Tuple[str, int]:
        pages, page_count = self.extract_pages(pdf_file_path)
        return "\n".join(pages), page_count

    def chunk_text(self, text: str, page_number: int = 1) -> List[Dict]:
        """Legacy single-page chunking wrapper. Uses new token/structure-aware chunker."""
        chunks, _ = chunk_pages(
            [PageText(page_number=page_number, text=text or "")],
            target_tokens=self.chunk_target_tokens,
            max_tokens=self.chunk_max_tokens,
            overlap_tokens=self.chunk_overlap_tokens,
            min_tokens=self.chunk_min_tokens,
        )
        return [
            {
                "index": c.chunk_index,
                "text": c.chunk_text,
                "page_number": c.page_number,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "char_count": c.character_count,
                "token_count": c.token_count,
                "section_heading": c.section_heading,
            }
            for c in chunks
        ]

    def build_document_chunks(self, pages: List[str]) -> Tuple[List[Dict], Dict]:
        page_objs = [PageText(page_number=i + 1, text=p or "") for i, p in enumerate(pages)]
        chunk_specs, stats = chunk_pages(
            page_objs,
            target_tokens=self.chunk_target_tokens,
            max_tokens=self.chunk_max_tokens,
            overlap_tokens=self.chunk_overlap_tokens,
            min_tokens=self.chunk_min_tokens,
        )
        out = []
        for c in chunk_specs:
            out.append({
                "index": c.chunk_index,
                "text": c.chunk_text,
                "page_number": c.page_number,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "char_count": c.character_count,
                "token_count": c.token_count,
                "section_heading": c.section_heading,
            })
        return out, stats
    
    @staticmethod
    def _embedding_progress(processed_chunks: int, total_chunks: int) -> int:
        if total_chunks <= 0:
            return 40
        # 40-80% range based on actual embedded chunk progress
        return 40 + int((processed_chunks / total_chunks) * 40)

    def _update_progress(self, document_id: int, **fields) -> None:
        from documents.models import Document

        update_fields = []
        for key, value in fields.items():
            if value is not None:
                update_fields.append(key)
        if update_fields:
            Document.objects.filter(pk=document_id).update(**fields)

    def process_document(self, document_id: int) -> Dict:
        """
        Process a single HR document: extract text, chunk, generate embeddings, store.
        """
        from django.db import transaction
        from documents.models import Document, DocumentChunk

        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist as exc:
            raise ValueError(f"Document with id {document_id} not found") from exc

        from django.utils import timezone
        try:
            # Do not reset attempt counter; it is owned by upload/retry endpoint.
            self._update_progress(
                document_id,
                status="processing",
                processing_error="",
                processing_progress=10,
                processing_stage="started",
                processing_stage_detail="Processing started.",
                total_chunks=0,
                processed_chunks=0,
                processing_completed_at=None,
                processing_started_at=timezone.now(),
            )

            pages, page_count = self.extract_pages(document.file.path)
            normalized_pages = [normalize_text(p) for p in pages]
            chunk_specs, stats = self.build_document_chunks(normalized_pages)
            self._update_progress(
                document_id,
                page_count=page_count,
                extracted_characters=int(stats.get("total_extracted_characters", 0)),
                extracted_tokens=int(stats.get("total_extracted_tokens", 0)),
                extraction_tokenizer=str(stats.get("tokenizer", "") or "")[:64],
                processing_progress=25,
                processing_stage="extracting",
                processing_stage_detail=f"Extracted text from {page_count} page(s).",
            )

            total_chunks = len(chunk_specs)
            self._update_progress(
                document_id,
                total_chunks=total_chunks,
                processed_chunks=0,
                processing_progress=40 if total_chunks > 0 else 40,
                processing_stage="chunking",
                processing_stage_detail=f"Created {total_chunks} chunk(s) ({stats.get('tokenizer','tokenizer')}).",
            )

            if not chunk_specs:
                raise RuntimeError("No extractable text chunks were generated from the document.")

            chunk_objects = []
            for i, chunk_spec in enumerate(chunk_specs, start=1):
                embedding = self.embedding_generator.generate_embedding(chunk_spec["text"])
                if len(embedding) != 3072:
                    raise RuntimeError(
                        f"Unexpected embedding dimension: {len(embedding)}, expected 3072"
                    )
                chunk_objects.append(
                    DocumentChunk(
                        document=document,
                        chunk_index=chunk_spec["index"],
                        chunk_text=chunk_spec["text"],
                        page_number=chunk_spec.get("page_number") or chunk_spec.get("page_start") or 1,
                        page_start=chunk_spec.get("page_start") or chunk_spec.get("page_number") or 1,
                        page_end=chunk_spec.get("page_end") or chunk_spec.get("page_number") or 1,
                        char_count=int(chunk_spec.get("char_count") or len(chunk_spec["text"])),
                        token_count=int(chunk_spec.get("token_count") or 0),
                        section_heading=(chunk_spec.get("section_heading") or "")[:255],
                        embedding_status="embedded",
                        embedding=embedding,
                    )
                )
                self._update_progress(
                    document_id,
                    processed_chunks=i,
                    total_chunks=total_chunks,
                    processing_progress=self._embedding_progress(i, total_chunks),
                    processing_stage="embedding",
                    processing_stage_detail=f"Embedded {i}/{total_chunks} chunk(s).",
                )

            self._update_progress(
                document_id,
                processing_progress=90,
                processing_stage="storing",
                processing_stage_detail="Storing embeddings in database.",
            )

            with transaction.atomic():
                DocumentChunk.objects.filter(document=document).delete()
                DocumentChunk.objects.bulk_create(chunk_objects)
                stored_count = DocumentChunk.objects.filter(document=document).count()
                if stored_count != total_chunks:
                    raise RuntimeError(
                        f"Chunk storage mismatch: expected {total_chunks}, stored {stored_count}"
                    )
                Document.objects.filter(pk=document.pk).update(
                    status="ready",
                    processing_error="",
                    page_count=page_count,
                    extracted_characters=int(stats.get("total_extracted_characters", 0)),
                    extracted_tokens=int(stats.get("total_extracted_tokens", 0)),
                    extraction_tokenizer=str(stats.get("tokenizer", "") or "")[:64],
                    processing_progress=100,
                    processing_stage="ready",
                    processing_stage_detail="Document ready for RAG.",
                    total_chunks=total_chunks,
                    processed_chunks=total_chunks,
                    processing_completed_at=timezone.now(),
                )

            document.refresh_from_db(fields=[
                "status", "processing_error", "page_count",
                "extracted_characters", "extracted_tokens", "extraction_tokenizer",
                "processing_progress", "processing_stage", "processing_stage_detail",
                "total_chunks", "processed_chunks",
            ])
            return {
                "document_id": document.id,
                "chunks_created": len(chunk_objects),
                "pages_processed": page_count,
                "extracted_characters": document.extracted_characters,
                "extracted_tokens": document.extracted_tokens,
                "tokenizer": stats.get("tokenizer"),
                "status": document.status,
            }
        finally:
            self.close()
    
    def answer_question(self, question: str) -> Dict:
        """
        Answer a question using the RAG pipeline.
        """
        from documents.models import DocumentChunk

        try:
            question_embedding = self.embedding_generator.generate_embedding(question)

            chunks = DocumentChunk.objects.select_related("document").all()
            chunk_embeddings = []
            chunk_metadata = []
            for chunk in chunks:
                chunk_embeddings.append(chunk.embedding)
                chunk_metadata.append(
                    {
                        "document_id": chunk.document.id,
                        "document_title": chunk.document.title,
                        "chunk_index": chunk.chunk_index,
                        "page_number": chunk.page_number,
                        "page_start": getattr(chunk, "page_start", None) or chunk.page_number,
                        "page_end": getattr(chunk, "page_end", None) or chunk.page_number,
                        "section_heading": getattr(chunk, "section_heading", "") or "",
                        "chunk_text": chunk.chunk_text,
                    }
                )

            retrieved = retrieve_top_chunks(
                query_embedding=question_embedding,
                chunk_embeddings=chunk_embeddings,
                chunk_metadata=chunk_metadata,
                similarity_threshold=self.similarity_threshold,
                retrieval_limit=self.retrieval_limit,
                use_pgvector=self.use_pgvector,
            )

            if not retrieved:
                return {
                    "answer": "I'm sorry, but I couldn't find relevant information in the HR policy documents to answer your question. Please make sure the policies have been uploaded and processed.",
                    "sources": [],
                    "references": [],
                }

            context_parts = []
            sources = []
            for i, result in enumerate(retrieved, start=1):
                chunk_text = result.get("chunk_text", "")
                doc_title = result.get("document_title", "Unknown")
                page_num = result.get("page_number", "Unknown")
                page_start = result.get("page_start") or page_num
                page_end = result.get("page_end") or page_num
                section_heading = result.get("section_heading") or ""
                doc_id = result.get("document_id")
                heading_part = f" | section={section_heading}" if section_heading else ""
                context_parts.append(
                    f"[S{i} | document_id={doc_id} | title={doc_title} | pages={page_start}-{page_end}{heading_part}]\n{chunk_text}"
                )
                sources.append(
                    {
                        "document_id": doc_id,
                        "document_title": doc_title,
                        "page_number": page_start if page_start == page_end else page_start,
                        "page_start": page_start,
                        "page_end": page_end,
                        "section_heading": section_heading,
                        "excerpt": chunk_text[:240] + "..." if len(chunk_text) > 240 else chunk_text,
                    }
                )

            context = "\n\n".join(context_parts)
            answer = self._generate_answer_with_gemini(question, context)
            return {"answer": answer, "sources": sources, "references": retrieved}
        finally:
            self.close()
    
    @staticmethod
    def _sanitize_error(exc: Exception) -> str:
        msg = str(exc).strip().replace("\n", " ")
        msg = " ".join(msg.split())
        return msg[:300] if msg else exc.__class__.__name__

    def _is_transient_generation_error(self, exc: Exception) -> bool:
        import google.genai.errors as genai_errors
        import httpx

        if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError, httpx.TransportError, genai_errors.ServerError)):
            return True
        if isinstance(exc, genai_errors.ClientError):
            status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
            text = str(exc).lower()
            return status == 429 or "resource_exhausted" in text or "rate" in text
        text = str(exc).lower()
        return any(m in text for m in ["timeout", "timed out", "temporarily unavailable", "503", "502", "504", "handshake"])

    def _generate_answer_with_gemini(self, question: str, context: str) -> str:
        """Generate a context-grounded answer using Google Gemini API."""
        import google.genai as genai
        from google.genai import types as genai_types

        client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=genai_types.HttpOptions(timeout=int(os.getenv("GEMINI_GENERATION_TIMEOUT_MS", "60000"))),
        )

        prompt = f"""You are an HR Policy Assistant. Answer the user's question using ONLY the provided context.

Rules:
- Answer the exact question directly. Be concise by default; add detail only when relevant.
- No unnecessary introductions, repetition, or long filler paragraphs.
- Use clear Markdown formatting: short headings, bullet/numbered lists, and Markdown tables only when they improve readability.
- Adapt format to question type: skills -> categorized table/bullets; experience -> concise bullets/table; policy -> direct answer then relevant rules/conditions; comparison -> comparison table; definition -> short explanation.
- Do not force every answer into a table.
- Never mix information from different candidates or documents. If context contains multiple candidates/resumes, only use information relevant to the requested candidate; if ambiguous, state the ambiguity and separate by document/candidate.
- Never invent facts, sources, page numbers, or document names. Use only retrieved context.
- If requested information is not in context, clearly state: "The uploaded documents do not contain that information."
- Every factual claim must be grounded in the provided context. Do not fabricate citations.
- Do NOT include a "Sources" section in the answer body; sources are displayed separately by the UI.

Context (each block has S# metadata):
{context}

User question: {question}

Answer:"""
        models_to_try = [self.gen_model] + [m for m in self.gen_fallback_models if m != self.gen_model]
        last_exc = None
        for model_name in models_to_try:
            for attempt in range(self.gen_max_retries):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    if response and getattr(response, "text", None):
                        return response.text
                    return "I apologize, but I was unable to generate a response. Please try again later."
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                    text = str(exc).lower()
                    model_unavailable = status == 404 or "no longer available" in text or "not found" in text
                    if model_unavailable:
                        logger.warning("Gemini generation model unavailable (%s): %s", model_name, self._sanitize_error(exc))
                        break
                    if not self._is_transient_generation_error(exc) or attempt >= self.gen_max_retries - 1:
                        raise RuntimeError(f"Gemini API error: {self._sanitize_error(exc)}") from exc
                    delay = min(20.0, (2 ** attempt)) * (0.5 + random.random() * 0.5)
                    logger.warning(
                        "Transient Gemini generation failure (%s, attempt %s/%s, retry_in=%.2fs): %s",
                        model_name,
                        attempt + 1,
                        self.gen_max_retries,
                        delay,
                        self._sanitize_error(exc),
                    )
                    time.sleep(delay)

        raise RuntimeError(f"Gemini API error: {self._sanitize_error(last_exc)}") from last_exc