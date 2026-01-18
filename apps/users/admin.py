import csv
from io import TextIOWrapper

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin

from .models import AllowedStudent, StudentImport, User


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


@admin.register(StudentImport)
class StudentImportAdmin(admin.ModelAdmin):
    list_display = ["uploaded_at", "processed"]
    readonly_fields = ["processed", "log_message"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.processed:
            return

        try:
            # 開啟上傳的檔案
            csv_file = TextIOWrapper(obj.csv_file.file, encoding="utf-8")
            reader = csv.DictReader(csv_file)

            created_count = 0
            skipped_count = 0
            logs = []

            User = get_user_model()

            for row in reader:
                student_id = row.get("student_id", "").strip().upper()
                name = row.get("name", "").strip()
                email = row.get("email", "").strip()
                grade = row.get("grade", "1").strip()

                if not student_id:
                    continue

                # 建立或取得使用者
                user, created = User.objects.get_or_create(
                    student_id=student_id,  # 用學號當帳號
                    defaults={
                        "first_name": name,
                        "email": email,
                        "grade": grade,
                        "is_active": True,
                    },
                )

                if created:
                    user.set_password(student_id)  # 預設密碼 = 學號
                    user.save()
                    created_count += 1
                    logs.append(f"新增: {student_id} {name}")
                else:
                    skipped_count += 1

            # 更新處理結果
            obj.processed = True
            obj.log_message = (
                f"成功新增: {created_count} 筆\n重複跳過: {skipped_count} 筆\n\n詳細紀錄:\n"
                + "\n".join(logs)
            )
            obj.save()

            messages.success(request, f"匯入成功！新增了 {created_count} 位學生。")

        except Exception as e:
            messages.error(request, f"匯入失敗: {str(e)}")
            obj.log_message = f"錯誤: {str(e)}"
            obj.save()
