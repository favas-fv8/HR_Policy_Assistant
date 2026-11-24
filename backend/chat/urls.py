"""HR Policy Assistant - Chat API URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "chat-api"

router = DefaultRouter(trailing_slash=False)
router.register(r"", ChatViewSet, basename="chat")

urlpatterns = [
    path("", include(router.urls)),
]