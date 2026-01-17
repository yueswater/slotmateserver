from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .enums import AppointmentStatus


class Appointment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="預約學生",
        null=True,
        blank=True,
    )
    date = models.DateField()
    time_slot = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.SCHEDULED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reason = models.TextField(blank=True, null=True, verbose_name="預約事由")
    rejection_reason = models.TextField(
        blank=True, null=True, verbose_name="拒絕預約理由"
    )

    class Meta:
        verbose_name = "預約紀錄"
        verbose_name_plural = "預約紀錄表"
        unique_together = ("date", "time_slot")
        ordering = ["-date", "time_slot"]

    def __str__(self):
        user_display = self.user if self.user else "尚未有學生預約"
        return f"{self.date} {self.time_slot} ({user_display})"
