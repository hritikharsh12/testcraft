from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user so the project isn't locked into Django's default table —
    industrial projects almost always need this room to grow (roles, plan
    tier, org membership, etc.) and it's painful to add later.
    """

    class Role(models.TextChoices):
        DEVELOPER = "developer", "Developer"
        REVIEWER = "reviewer", "Reviewer"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.DEVELOPER)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username
