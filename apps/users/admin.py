from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin

from .models import AllowedStudent, User


@admin.register(AllowedStudent)
class AllowedStudentAdmin(ModelAdmin):
    list_display = ("student_id", "full_name")
    search_fields = ("student_id", "full_name")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "student_id",
        "first_name",
        "last_name",
        "department",
        "grade",
        "is_staff",
    )
    search_fields = ("student_id", "first_name", "last_name", "email")

    fieldsets = (
        (None, {"fields": ("student_id", "password")}),
        (
            "個人資訊",
            {"fields": ("first_name", "last_name", "email", "department", "grade")},
        ),
        (
            "權限",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("重要日期", {"fields": ("last_login", "date_joined")}),
    )

    ordering = ["student_id"]
