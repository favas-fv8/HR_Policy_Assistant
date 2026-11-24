"""HR Policy Assistant - Documents API URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "documents-api"

router = DefaultRouter(trailing_slash=False)
router.register(r"documents", views.DocumentViewSet, basename="documents")

urlpatterns = router.urls