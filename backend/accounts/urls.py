"""HR Policy Assistant - Accounts API URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "accounts-api"

router = DefaultRouter(trailing_slash=False)
router.register(r"users", views.UserViewSet, basename="users")
router.register(r"profile", views.EmployeeProfileViewSet, basename="profile")

urlpatterns = router.urls