"""HR Policy Assistant - RAG API URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "rag-api"

router = DefaultRouter(trailing_slash=False)
router.register(r"", RagViewSet, basename="rag")

urlpatterns = [
    path("", include(router.urls)),
]