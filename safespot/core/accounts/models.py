from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


# ---------------------------
# Custom User Manager
# ---------------------------
class UserManager(BaseUserManager):

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username must be set")

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        # ✅ Django permissions
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        # 🔥 FORCE ADMIN ROLE
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(username, password, **extra_fields)


# ---------------------------
# Custom User Model
# ---------------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ("client", "Client"),
        ("admin", "Admin"),
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="client"
    )

    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    objects = UserManager()

    def __str__(self):
        return self.username


# ---------------------------
# Profile Model
# ---------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    # Extra user details
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)

    # Points will be calculated from confirmed incidents
    def get_points(self):
        """
        Calculate points based on confirmed incidents.
        For every 2 incidents created by this user that get confirmed, give 1 point.
        """
        from incidents.models import Accident

        # Get all accidents created by this user
        user_accidents = Accident.objects.filter(created_by=self.user, is_confirmed=True)
        confirmed_count = user_accidents.count()

        # Calculate points: 1 point for every 2 confirmed incidents
        return confirmed_count // 2

    def __str__(self):
        return f"Profile of {self.user.username}"
