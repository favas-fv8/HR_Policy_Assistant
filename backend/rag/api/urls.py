from rest_framework.routers import DefaultRouter
from . import views

app_name = "rag-api"

router = DefaultRouter(trailing_slash=False)
router.register(r"rag", RagViewSet, basename="rag")

urlpatterns = router.urls