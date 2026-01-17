import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = "匯入學生帳號 (自動生成 Email 與預設密碼)"

    def handle(self, *args, **kwargs):
        base_dir = settings.BASE_DIR
        file_path = os.path.join(base_dir, "data", "students.csv")

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"找不到檔案: {file_path}"))
            return

        with open(file_path, "r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            count = 0

            for row in reader:
                student_id = row["student_id"]
                first_name = row["first_name"]
                last_name = row["last_name"]

                generated_email = f"{student_id}@nccu.edu.tw"
                default_password = student_id

                if User.objects.filter(student_id=student_id).exists():
                    self.stdout.write(self.style.WARNING(f"跳過已存在: {student_id}"))
                    continue

                User.objects.create_user(
                    student_id=student_id,
                    email=generated_email,
                    password=default_password,
                    first_name=first_name,
                    last_name=last_name,
                    grade=1,
                    is_first_login=True,
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"成功匯入 {count} 筆學生資料！"))
