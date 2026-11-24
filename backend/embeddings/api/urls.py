from rest_framework.routers import DefaultRouter
from . import views

app_name = "embeddings-api"

router = DefaultRouter(trailing_slash=False)
router.register(r"embeddings", EmbeddingViewSet, basename="embeddings")

urlpatterns = router.urls