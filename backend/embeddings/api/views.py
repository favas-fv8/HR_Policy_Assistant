from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings

from embeddings.generator import EmbeddingGenerator


class EmbeddingViewSet(viewsets.ViewSet):
    """Gemini embedding generation endpoints."""
    
    def list(self, request):
        """List embedding service status."""
        return Response({
            "service": "Google Gemini Embedding",
            "model": "text-embedding-004",
            "dimension": 3072,
            "status": "ready"
        })
    
    @action(methods=["post"], detail=False)
    def generate(self, request):
        """Generate embedding for a text."""
        text = request.data.get("text", "").strip()
        if not text:
            return Response(
                {"error": "Text parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            generator = EmbeddingGenerator(api_key=settings.GEMINI_API_KEY)
            embedding = generator.generate_embedding(text)
            return Response({
                "embedding": embedding,
                "dimension": len(embedding),
                "model": "text-embedding-004"
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )