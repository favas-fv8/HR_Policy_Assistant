from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings

from rag.pipeline import RAGPipeline


class RagViewSet(viewsets.ViewSet):
    """RAG-powered HR Policy Assistant endpoints."""

    def list(self, request):
        """List RAG pipeline status."""
        pipeline = RAGPipeline()
        return Response({
            "pipeline": "HR Policy Assistant RAG",
            "similarity_threshold": pipeline.similarity_threshold,
            "retrieval_limit": pipeline.retrieval_limit,
            "chunk_size": pipeline.chunk_size,
            "chunk_overlap": pipeline.chunk_overlap,
            "status": "ready"
        })

    @action(methods=["post"], detail=False)
    def ask(self, request):
        """Ask a question about HR policies using RAG."""
        question = request.data.get("question", "").strip()
        if not question:
            return Response(
                {"error": "Question parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pipeline = RAGPipeline()
            result = pipeline.answer_question(question)
            return Response({
                "answer": result["answer"],
                "sources": result["sources"],
                "reference_count": len(result["references"])
            })
        except Exception as e:
            return Response(
                {"error": f"RAG pipeline error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(methods=["post"], detail=False)
    def process_document(self, request):
        """Process a document through the RAG pipeline."""
        document_id = request.data.get("document_id")
        if not document_id:
            return Response(
                {"error": "document_id parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pipeline = RAGPipeline()
            result = pipeline.process_document(document_id)
            return Response(result)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
