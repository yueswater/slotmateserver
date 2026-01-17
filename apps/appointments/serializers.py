from django.db import transaction
from rest_framework import serializers

from .enums import AppointmentStatus
from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source="user.student_id", read_only=True)
    student_name = serializers.CharField(source="user.first_name", read_only=True)
    student_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "date",
            "time_slot",
            "status",
            "reason",
            "rejection_reason",
            "student_id",
            "student_name",
            "student_email",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at", "student_id", "student_name", "student_email"]


class CreateAppointmentSerializer(serializers.Serializer):
    date = serializers.DateField()
    time_slots = serializers.ListField(
        child=serializers.CharField(), max_length=4, allow_empty=False
    )
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        date = validated_data["date"]
        slots = validated_data["time_slots"]
        reason = validated_data.get("reason", "")

        created_appointments = []
        try:
            with transaction.atomic():
                # 檢查並建立多個預約
                for slot in slots:
                    # 檢查該時段是否已被預約
                    if Appointment.objects.filter(
                        date=date, time_slot=slot, status=AppointmentStatus.SCHEDULED
                    ).exists():
                        raise serializers.ValidationError(f"{slot} 時段已被預約")
                    # 建立預約
                    appt = Appointment.objects.create(
                        user=user,
                        date=date,
                        time_slot=slot,
                        reason=reason,
                        status=AppointmentStatus.SCHEDULED,
                    )
                    created_appointments.append(appt)
        except Exception as e:
            raise serializers.ValidationError(str(e))

        return created_appointments
