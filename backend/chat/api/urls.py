from rest_framework.routers import DefaultRouter
from . import views

app_name = "chat-api"

router = DefaultRouter(trailing_slash=False)
router.register(r"chat", ChatViewSet, basename="chat")

urlpatterns = router.urls