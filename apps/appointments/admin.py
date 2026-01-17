from django.contrib import admin
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin
from unfold.decorators import action

from .enums import AppointmentStatus
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(ModelAdmin):

    list_display = [
        "get_student_info",
        "date",
        "time_slot",
        "custom_status_display",
        "created_at",
    ]
    list_filter = ["status", "date", "created_at"]
    search_fields = [
        "user__student_id",
        "user__first_name",
        "user__last_name",
        "reason",
    ]
    date_hierarchy = "date"
    ordering = ["-date", "time_slot"]

    def get_student_info(self, obj):
        if obj.user:
            return f"{obj.user.student_id} {obj.user.first_name} {obj.user.last_name}"

        return mark_safe('<span style="color: #999;">待預約 (釋出時段)</span>')

    get_student_info.short_description = "預約人資訊"

    def custom_status_display(self, obj):
        if obj.status == AppointmentStatus.SCHEDULED:
            return mark_safe('<b style="color: #E32636;">佔用中</b>')
        if obj.status == AppointmentStatus.AVAILABLE:
            return mark_safe('<b style="color: #009252;">可預約</b>')

        return obj.get_status_display()

    custom_status_display.short_description = "目前狀態"

    @action(description="標記為已完成")
    def mark_as_completed(self, request, queryset):
        queryset.update(status=AppointmentStatus.COMPLETED)

    @action(description="標記為已取消")
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status=AppointmentStatus.CANCELLED)
