import uuid
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    OPERATIONS = "OPERATIONS", "Operations"
    MANAGEMENT = "MANAGEMENT", "Management"


class MatnaUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # A superuser has full Django-admin access, so their application role must match.
        extra_fields.setdefault("role", UserRole.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.OPERATIONS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = MatnaUserManager()

    REQUIRED_FIELDS = ["email"]

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"