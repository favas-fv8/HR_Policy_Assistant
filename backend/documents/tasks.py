"""Background processing for uploaded HR policy documents.

There is no Celery broker in this project, so processing runs in a daemon
thread started by the upload view. The thread extracts PDF text, chunks it,
generates Gemini embeddings, and stores DocumentChunk rows via RAGPipeline.
"""

import logging
import traceback

logger = logging.getLogger(__name__)


def _safe_error_message(exc: Exception) -> str:
    """Return a short, non-sensitive error message for admins/UI."""
    msg = str(exc).strip().replace("\n", " ")
    if not msg:
        msg = exc.__class__.__name__
    # Avoid leaking very long/internal payloads
    return msg[:500]


def process_document_task(document_id: int) -> None:
    """Extract, chunk, embed and store a document's content."""
    from django.db import connection

    from documents.models import Document

    try:
        if not Document.objects.filter(pk=document_id).exists():
            logger.info("Skipping processing for missing document_id=%s (likely deleted).", document_id)
            return

        from rag.pipeline import RAGPipeline

        pipeline = RAGPipeline()
        pipeline.process_document(document_id)
        logger.info("Document %s processed successfully", document_id)
    except Document.DoesNotExist:
        logger.info("Document %s no longer exists; skipping processing result writes.", document_id)
    except Exception as exc:
        logger.exception("Failed to process document %s", document_id)
        try:
            from django.utils import timezone
            doc = Document.objects.filter(pk=document_id).first()
            if doc is None:
                logger.info("Document %s deleted during processing; skipping error status update.", document_id)
            else:
                current = int(getattr(doc, "processing_progress", 0) or 0)
                Document.objects.filter(pk=document_id).update(
                    status="error",
                    processing_error=_safe_error_message(exc),
                    processing_stage="error",
                    processing_stage_detail="Processing failed.",
                    processing_progress=min(max(current, 0), 99),
                    processing_completed_at=timezone.now(),
                )
        except Exception:
            logger.exception("Failed to mark document %s as error", document_id)
    finally:
        connection.close()
