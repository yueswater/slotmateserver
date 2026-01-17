from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    自訂使用者管理員，使用學號作為唯一識別欄位。
    """

    def create_user(self, student_id, password=None, **extra_fields):
        if not student_id:
            raise ValueError("必須提供學號 (Student ID)")

        email = self.normalize_email(extra_fields.pop("email", None))
        user = self.model(student_id=student_id, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, student_id, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(student_id, password, **extra_fields)


class AllowedStudent(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "允許註冊學生"
        verbose_name_plural = "允許註冊學生名單"

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"


class User(AbstractUser):
    username = None  # Remove username field
    student_id = models.CharField("學號", max_length=20, unique=True)
    department = models.CharField("系所", max_length=100)
    grade = models.PositiveIntegerField("年級")
    is_first_login = models.BooleanField("是否首次登入", default=True)
    last_logout = models.DateTimeField("最後登入時間", null=True, blank=True)
    last_login_ip = models.GenericIPAddressField("最後登入IP", null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "student_id"
    REQUIRED_FIELDS = ["email", "first_name", "last_name", "department", "grade"]

    class Meta:
        verbose_name = "使用者"
        verbose_name_plural = "使用者列表"

    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name}"
