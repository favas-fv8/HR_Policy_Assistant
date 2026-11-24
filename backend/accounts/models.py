from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """Custom User model with role-based access control."""
    ROLE_CHOICES = [
        ("hr_admin", "HR Admin"),
        ("employee", "Employee"),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="employee")
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    @property
    def is_hr_admin(self):
        return self.role == "hr_admin"
    
    @property
    def is_employee(self):
        return self.role == "employee"