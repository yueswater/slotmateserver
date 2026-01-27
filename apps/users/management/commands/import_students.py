import csv
import os
from django.core.management.base import BaseCommand
from users.models import User
from tqdm import tqdm

class Command(BaseCommand):
    help = "匯入學生帳號"

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **kwargs):
        file_path = kwargs['csv_file']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"找不到檔案: {file_path}"))
            return

        with open(file_path, "r", encoding="utf-8-sig") as csv_file:
            rows = list(csv.DictReader(csv_file))
            count = 0

            for row in tqdm(rows, desc="匯入進度"):
                student_id = row["student_id"].strip()
                name = row["name"].strip()
                email = row.get("email", f"{student_id}@nccu.edu.tw").strip()

                try:
                    student_year_prefix = int(student_id[:3])
                    calculated_grade = (114 - student_year_prefix) + 1
                except (ValueError, IndexError):
                    calculated_grade = 1

                if User.objects.filter(student_id=student_id).exists():
                    continue

                User.objects.create_user(
                    student_id=student_id,
                    email=email,
                    password=student_id,
                    first_name=name,
                    grade=calculated_grade,
                    is_first_login=True,
                    is_active=False
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"成功匯入 {count} 筆學生資料！"))