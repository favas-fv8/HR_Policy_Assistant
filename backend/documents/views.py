from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import FileResponse

from .serializers import (
    DocumentSerializer, DocumentUploadSerializer,
    DocumentChunkListSerializer, DocumentChunkSerializer
)
from .models import Document, DocumentChunk


class DocumentViewSet(viewsets.ViewSet):
    """HR Document management endpoints."""
    
    def list(self, request):
        """List all documents."""
        documents = Document.objects.all()
        serializer = DocumentSerializer(documents, many=True, context={"request": request})
        return Response(serializer.data)
    
    def create(self, request):
        """Upload a new HR policy document (HR Admin only)."""
        if not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied. HR Admin access required."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DocumentUploadSerializer(
            data=request.data,
        )
        if serializer.is_valid(raise_exception=True):
            from django.utils import timezone
            document = serializer.save(
                uploaded_by=request.user,
                status="started",
                processing_progress=0,
                processing_stage="uploaded",
                processing_stage_detail="Document uploaded.",
                processing_error="",
                total_chunks=0,
                processed_chunks=0,
                processing_attempt=1,
                processing_started_at=timezone.now(),
                processing_completed_at=None,
            )

            import threading
            from .tasks import process_document_task
            threading.Thread(
                target=process_document_task,
                args=(document.id,),
                daemon=True,
            ).start()

            return Response(
                DocumentSerializer(document, context={"request": request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        """Get document details."""
        document = get_object_or_404(Document, pk=pk)
        # Employees can view documents, HR Admin has full access
        # This is intentionally open as employees need to view policy documents
        serializer = DocumentSerializer(document, context={"request": request})
        return Response(serializer.data)

    @action(methods=["get"], detail=True)
    def status(self, request, pk=None):
        """Get live processing status/progress for a document."""
        document = get_object_or_404(Document, pk=pk)
        serializer = DocumentSerializer(document, context={"request": request})
        data = serializer.data
        return Response({
            "id": data["id"],
            "title": data["title"],
            "status": data["status"],
            "processing_progress": data["processing_progress"],
            "processing_stage": data["processing_stage"],
            "processing_stage_detail": data["processing_stage_detail"],
            "total_chunks": data["total_chunks"],
            "processed_chunks": data["processed_chunks"],
            "chunk_count": data["chunk_count"],
            "embedded_chunk_count": data.get("embedded_chunk_count", 0),
            "extracted_characters": data.get("extracted_characters", 0),
            "extracted_tokens": data.get("extracted_tokens", 0),
            "extraction_tokenizer": data.get("extraction_tokenizer", ""),
            "page_count": data["page_count"],
            "file_size": data["file_size"],
            "processing_error": data["processing_error"],
            "processing_attempt": data["processing_attempt"],
            "processing_started_at": data["processing_started_at"],
            "processing_completed_at": data["processing_completed_at"],
        })

    @action(methods=["get"], detail=True, url_path="file")
    def file(self, request, pk=None):
        """Serve the actual PDF file (authenticated)."""
        document = get_object_or_404(Document, pk=pk)
        if not document.file:
            return Response({"error": "Document file not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            fh = document.file.open("rb")
        except Exception:
            return Response({"error": "Document file not found."}, status=status.HTTP_404_NOT_FOUND)
        filename = document.filename or document.file.name.rsplit("/", 1)[-1] or f"document-{document.id}.pdf"
        resp = FileResponse(fh, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="{filename}"'
        return resp
    
    @action(methods=["delete"], detail=True)
    def delete(self, request, pk=None):
        """Delete a document (HR Admin only)."""
        if not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN
            )
        document = get_object_or_404(Document, pk=pk)
        document.delete()
        return Response(
            {"detail": "Document deleted successfully."},
            status=status.HTTP_200_OK,
        )

    @action(methods=["post"], detail=True)
    def reprocess(self, request, pk=None):
        """Retry processing a failed/stale document (HR Admin only)."""
        if not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied. HR Admin access required."},
                status=status.HTTP_403_FORBIDDEN
            )

        document = get_object_or_404(Document, pk=pk)
        if not document.file:
            return Response(
                {"error": "Document file is missing; cannot reprocess."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark as processing before background retry; task will set ready/error.
        from django.db.models import F
        from django.utils import timezone
        Document.objects.filter(pk=document.pk).update(
            status="started",
            processing_error="",
            processing_progress=10,
            processing_stage="started",
            processing_stage_detail="Reprocessing requested.",
            total_chunks=0,
            processed_chunks=0,
            processing_attempt=F("processing_attempt") + 1,
            processing_started_at=timezone.now(),
            processing_completed_at=None,
        )
        document.refresh_from_db()

        import threading
        from .tasks import process_document_task

        threading.Thread(
            target=process_document_task,
            args=(document.id,),
            daemon=True,
        ).start()

        return Response(
            {
                "detail": "Document reprocessing started.",
                "document_id": document.id,
                "status": document.status,
            },
            status=status.HTTP_202_ACCEPTED,
        )
    
    @action(methods=["get"], detail=True)
    def chunks(self, request, pk=None):
        """Get document chunks."""
        document = get_object_or_404(Document, pk=pk)
        # Employees can view chunks (they need this for RAG answers)
        # HR Admin has full access
        chunks = document.chunks.all()
        serializer = DocumentChunkListSerializer(chunks, many=True)
        return Response(serializer.data)