"""Django URL Configuration for hrproject project."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts.views import UserViewSet, EmployeeProfileViewSet
from documents.views import DocumentViewSet
from rag.views import RagViewSet
from chat.views import ChatViewSet

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # API v1 - Accounts
    path("api/v1/accounts/users/", UserViewSet.as_view({"get": "list", "post": "create"})),
    path("api/v1/accounts/users/me/", UserViewSet.as_view({"get": "me"})),
    path("api/v1/accounts/users/logout/", UserViewSet.as_view({"post": "logout"})),
    path("api/v1/accounts/users/<int:pk>/update/", UserViewSet.as_view({"patch": "update", "put": "update"})),
    path("api/v1/accounts/users/<int:pk>/deactivate/", UserViewSet.as_view({"post": "deactivate"})),
    path("api/v1/accounts/users/<int:pk>/reactivate/", UserViewSet.as_view({"post": "reactivate"})),
    path("api/v1/accounts/users/<int:pk>/delete/", UserViewSet.as_view({"delete": "destroy"})),
    path("api/v1/accounts/profile/", EmployeeProfileViewSet.as_view({"get": "retrieve"})),

    # API v1 - Documents
    path("api/v1/documents/", DocumentViewSet.as_view({"get": "list", "post": "create"})),
    path("api/v1/documents/<int:pk>/", DocumentViewSet.as_view({"get": "retrieve", "delete": "delete"})),
    path("api/v1/documents/<int:pk>/file/", DocumentViewSet.as_view({"get": "file"})),
    path("api/v1/documents/<int:pk>/chunks/", DocumentViewSet.as_view({"get": "chunks"})),
    path("api/v1/documents/<int:pk>/status/", DocumentViewSet.as_view({"get": "status"})),
    path("api/v1/documents/<int:pk>/reprocess/", DocumentViewSet.as_view({"post": "reprocess"})),

    # API v1 - RAG
    path("api/v1/rag/", RagViewSet.as_view({"get": "list"})),
    path("api/v1/rag/ask/", RagViewSet.as_view({"post": "ask"})),
    path("api/v1/rag/process/", RagViewSet.as_view({"post": "process_document"})),

    # API v1 - Chat
    path("api/v1/chat/conversations/", ChatViewSet.as_view({"get": "list_conversations"})),
    path("api/v1/chat/conversations/new/", ChatViewSet.as_view({"post": "create_conversation"})),
    path("api/v1/chat/conversations/<int:pk>/messages/", ChatViewSet.as_view({"get": "messages"})),
    path("api/v1/chat/conversations/<int:pk>/send/", ChatViewSet.as_view({"post": "send_message"})),
    path("api/v1/chat/conversations/<int:pk>/delete/", ChatViewSet.as_view({"delete": "delete_conversation"})),

    # Authentication - dj_rest_auth login/logout only (no registration)
    path("api/v1/auth/", include("dj_rest_auth.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
