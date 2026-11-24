from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404

from accounts.serializers import (
    UserSerializer, CustomUserCreateSerializer, EmployeeUpdateSerializer,
    EmployeeProfileSerializer, DocumentUploadSerializer
)
from accounts.models import CustomUser
from documents.models import Document
from documents.serializers import DocumentUploadSerializer as DocUploadSerializer


class UserViewSet(viewsets.ViewSet):
    """User management endpoints for HR Admin."""

    def list(self, request):
        """List all users (HR Admin only)."""
        if not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN
            )
        users = CustomUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Create new employee user (HR Admin only)."""
        if not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN
            )
        # Roles are enforced server-side in serializer.create().
        serializer = CustomUserCreateSerializer(
            data=request.data,
            context={"request": request}
        )
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["get"], detail=False)
    def me(self, request):
        """Current user profile."""
        serializer = EmployeeProfileSerializer(request.user)
        return Response(serializer.data)

    @action(methods=["post"], detail=False)
    def logout(self, request):
        """Logout user."""
        logout(request)
        return Response({"detail": "Successfully logged out."})

    @action(methods=["patch", "put"], detail=True)
    def update(self, request, pk=None):
        """Update employee profile details (HR Admin only)."""
        if not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN
            )
        employee = get_object_or_404(CustomUser, pk=pk)
        if employee.is_hr_admin:
            return Response(
                {"error": "HR Admin accounts cannot be edited through this endpoint."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        partial = request.method.lower() == "patch"
        serializer = EmployeeUpdateSerializer(employee, data=request.data, partial=partial)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(UserSerializer(employee).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["post"], detail=True)
    def deactivate(self, request, pk=None):
        """Deactivate employee account (HR Admin only)."""
        if not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN
            )
        employee = get_object_or_404(CustomUser, pk=pk)
        if employee.pk == request.user.pk:
            return Response({"error": "You cannot deactivate your own account."}, status=status.HTTP_400_BAD_REQUEST)
        if employee.is_hr_admin:
            return Response({"error": "HR Admin accounts cannot be deactivated through this endpoint."}, status=status.HTTP_400_BAD_REQUEST)
        employee.is_active = False
        employee.save(update_fields=["is_active"])
        return Response(UserSerializer(employee).data)

    @action(methods=["post"], detail=True)
    def reactivate(self, request, pk=None):
        """Reactivate employee account (HR Admin only)."""
        if not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN
            )
        employee = get_object_or_404(CustomUser, pk=pk)
        if employee.is_hr_admin:
            return Response({"error": "HR Admin accounts cannot be modified through this endpoint."}, status=status.HTTP_400_BAD_REQUEST)
        employee.is_active = True
        employee.save(update_fields=["is_active"])
        return Response(UserSerializer(employee).data)

    def destroy(self, request, pk=None):
        """Permanently delete an employee account (HR Admin only).

        Safe-guarded: refuses to delete HR admins, self, or accounts with
        associated chat/document history; deactivation should be used instead.
        """
        if not request.user.is_hr_admin:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        employee = get_object_or_404(CustomUser, pk=pk)
        if employee.pk == request.user.pk:
            return Response({"error": "You cannot delete your own account."}, status=status.HTTP_400_BAD_REQUEST)
        if employee.is_hr_admin:
            return Response({"error": "HR Admin accounts cannot be deleted."}, status=status.HTTP_400_BAD_REQUEST)

        related = []
        if hasattr(employee, "conversations") and employee.conversations.exists():
            related.append("chat conversations/messages")
        if hasattr(employee, "uploaded_documents") and employee.uploaded_documents.exists():
            related.append("uploaded documents")
        if related:
            return Response(
                {
                    "error": "Cannot permanently delete this employee because associated records exist.",
                    "related_records": related,
                    "detail": "Deactivate the account instead to preserve chat and document history.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        username = employee.username
        employee.delete()
        return Response({"detail": f"Employee {username} deleted."}, status=status.HTTP_200_OK)


class EmployeeProfileViewSet(viewsets.ViewSet):
    """Employee profile endpoint."""

    def retrieve(self, request, pk=None):
        """Get employee profile by ID (HR Admin) or current user."""
        if request.user.is_hr_admin:
            user = get_object_or_404(CustomUser, pk=pk)
        else:
            user = request.user
        serializer = EmployeeProfileSerializer(user)
        return Response(serializer.data)
