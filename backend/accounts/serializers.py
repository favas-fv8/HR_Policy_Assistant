from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import CustomUser
from documents.models import Document, DocumentChunk

CustomUser = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUser model."""
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    role = serializers.CharField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id", "username", "email", "full_name", "role", "employee_id",
            "is_active", "date_joined", "last_login"
        ]
        read_only_fields = ["date_joined", "last_login"]


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new employee accounts (HR Admin only)."""
    password = serializers.CharField(write_only=True, required=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, required=True, trim_whitespace=False)
    full_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)

    class Meta:
        model = CustomUser
        fields = [
            "username", "email", "password", "confirm_password",
            "role", "employee_id", "full_name", "first_name", "last_name"
        ]
        extra_kwargs = {
            "email": {"required": False, "allow_blank": True},
            "employee_id": {"required": True},
            "role": {"read_only": True},
        }

    def validate_employee_id(self, value):
        employee_id = (value or "").strip()
        if not employee_id:
            raise serializers.ValidationError("This field is required.")
        # Exact, case-sensitive uniqueness/preservation.
        if CustomUser.objects.filter(employee_id__exact=employee_id).exists():
            raise serializers.ValidationError("An account with this Employee ID already exists.")
        return employee_id

    def validate_email(self, value):
        email = (value or "").strip()
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate(self, data):
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if password is None or password == "":
            raise serializers.ValidationError({"password": ["This field is required."]})
        if confirm_password is None or confirm_password == "":
            raise serializers.ValidationError({"confirm_password": ["This field is required."]})
        if password != confirm_password:
            raise serializers.ValidationError({"confirm_password": ["Passwords do not match."]})

        employee_id = (data.get("employee_id") or "").strip()
        if not employee_id:
            raise serializers.ValidationError({"employee_id": ["This field is required."]})
        data["employee_id"] = employee_id

        # Employee ID is the login User ID; preserve exact value as entered.
        username = employee_id
        if CustomUser.objects.filter(username__exact=username).exists():
            raise serializers.ValidationError({"employee_id": ["An account with this Employee ID/User ID already exists."]})
        data["username"] = username

        full_name = (data.get("full_name") or "").strip()
        first_name = (data.get("first_name") or "").strip()
        last_name = (data.get("last_name") or "").strip()
        if full_name and not (first_name or last_name):
            parts = full_name.split()
            first_name = parts[0]
            last_name = " ".join(parts[1:])
        data["first_name"] = first_name
        data["last_name"] = last_name

        return data

    def create(self, validated_data):
        """Create employee user with exact Employee ID and securely hashed password."""
        password = validated_data.pop("password")
        validated_data.pop("confirm_password", None)
        validated_data.pop("full_name", None)
        validated_data.pop("role", None)

        # Enforce employee role; HR Admin is created only via management command.
        user = CustomUser(**validated_data, role="employee")
        user.set_password(password)  # hashes exact supplied password
        try:
            validate_password(password, user=user)
        except Exception as exc:
            errors = getattr(exc, "messages", None) or ["This password does not meet the security requirements."]
            raise serializers.ValidationError({"password": list(errors)})
        user.save()
        return user


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating employee profile details (HR Admin)."""
    full_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = ["employee_id", "username", "email", "first_name", "last_name", "full_name"]
        extra_kwargs = {
            "employee_id": {"required": False},
            "username": {"required": False, "trim_whitespace": False},
            "email": {"required": False, "allow_blank": True},
            "first_name": {"required": False, "allow_blank": True},
            "last_name": {"required": False, "allow_blank": True},
        }

    def validate_employee_id(self, value):
        employee_id = (value or "").strip()
        if not employee_id:
            raise serializers.ValidationError("This field is required.")
        qs = CustomUser.objects.filter(employee_id__exact=employee_id)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("An account with this Employee ID already exists.")
        return employee_id

    def validate_email(self, value):
        email = (value or "").strip()
        if email:
            qs = CustomUser.objects.filter(email__iexact=email)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate(self, data):
        full_name = (data.pop("full_name", None) or "").strip()
        if full_name and not (data.get("first_name") or data.get("last_name")):
            parts = full_name.split()
            data["first_name"] = parts[0]
            data["last_name"] = " ".join(parts[1:])

        employee_id = data.get("employee_id")
        if employee_id is not None:
            employee_id = (employee_id or "").strip()
            data["employee_id"] = employee_id
            data["username"] = employee_id  # keep username consistent with Employee ID rule, exact value
            qs = CustomUser.objects.filter(username__exact=employee_id)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"employee_id": ["An account with this Employee ID/User ID already exists."]})
        else:
            # Never allow direct username drift from Employee ID via this endpoint.
            data.pop("username", None)
        return data


class EmployeeProfileSerializer(serializers.ModelSerializer):
    """Serializer for employee profile view."""
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id", "username", "email", "full_name", "employee_id",
            "is_active", "role", "date_joined", "last_login"
        ]
        read_only_fields = ["role", "employee_id", "date_joined", "last_login"]


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for document upload (HR Admin only)."""

    class Meta:
        model = CustomUser  # Placeholder - will be updated when docs app is properly configured
        fields = ["title", "file"]

    def validate_file(self, value):
        """Validate uploaded file is PDF and within size limits."""
        import os
        from django.conf import settings

        ext = os.path.splitext(value.name).lower()
        if ext != ".pdf":
            raise serializers.ValidationError("Only PDF files are allowed.")

        max_size = getattr(settings, "MAX_DOCUMENT_FILE_SIZE", 10 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError(f"File size must be under {max_size // (1024 * 1024)}MB.")

        return value

    def create(self, validated_data):
        """Populate required model fields (filename, file_size) from the upload."""
        uploaded = validated_data.get("file")
        if uploaded is not None:
            validated_data.setdefault("filename", uploaded.name)
            validated_data.setdefault("file_size", uploaded.size)
        return super().create(validated_data)


class DocumentChunkListSerializer(serializers.ModelSerializer):
    """Serializer for listing document chunks with metadata."""

    document_title = serializers.CharField(source="document.title", read_only=True)
    chunk_text_length = serializers.SerializerMethodField()

    class Meta:
        model = DocumentChunk
        fields = [
            "chunk_index", "page_number", "created_at",
            "document_title", "chunk_text_length"
        ]

    def get_chunk_text_length(self, obj):
        return len(obj.chunk_text)
