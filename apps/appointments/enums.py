from django.db import models


class AppointmentStatus(models.TextChoices):
    AVAILABLE = "available", "可預約"
    SCHEDULED = "scheduled", "已預約"
    CONFIRMED = "confirmed", "已確認"
    COMPLETED = "completed", "已完成"
    CANCELLED = "cancelled", "已取消"
