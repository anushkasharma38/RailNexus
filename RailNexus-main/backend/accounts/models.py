from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        ENGINEERING = "ENGINEERING", "Engineering"
        TRACTION = "TRACTION", "Traction"
        S_AND_T = "S_AND_T", "S&T"
        CONTROL_OFFICE = "CONTROL_OFFICE", "Control Office"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ENGINEERING)
    department = models.CharField(max_length=80, blank=True)
