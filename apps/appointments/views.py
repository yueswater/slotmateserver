from datetime import timedelta

from django.db import models, transaction
from django.utils import timezone
from notify_letter.utils import (
    send_confirmation_email,
    send_notification_email,
    send_rejection_email,
)
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .enums import AppointmentStatus
from .models import Appointment
from .serializers import AppointmentSerializer, CreateAppointmentSerializer


class AdminReleaseSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment

        fields = ["date", "time_slot"]


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAdminOrReadOnly]

    http_method_names = ["get", "post", "patch", "head", "options", "put"]

    def get_serializer_class(self):

        if self.action == "create" and isinstance(self.request.data, list):
            return AdminReleaseSlotSerializer

        if self.action == "create":
            return CreateAppointmentSerializer

        return AppointmentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Appointment.objects.all()
        if self.action == "book":
            return Appointment.objects.filter(status=AppointmentStatus.AVAILABLE)
        status_param = self.request.query_params.get("status")
        if status_param == "available":
            return Appointment.objects.filter(status=AppointmentStatus.AVAILABLE)

        return Appointment.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        is_many = isinstance(request.data, list)

        if is_many:
            created_count = 0
            skipped_count = 0
            errors = []

            for item in request.data:
                date = item.get("date")
                time_slot = item.get("time_slot")

                if Appointment.objects.filter(date=date, time_slot=time_slot).exists():
                    skipped_count += 1
                    continue

                serializer = self.get_serializer(data=item)

                if serializer.is_valid():
                    serializer.save(status=AppointmentStatus.AVAILABLE, user=None)
                    created_count += 1
                else:
                    errors.append(serializer.errors)

            if created_count == 0 and len(errors) > 0:
                return Response(
                    {"message": "所有時段建立失敗", "errors": errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {
                    "message": f"成功釋出 {created_count} 個時段，跳過 {skipped_count} 個重複時段",
                    "created": created_count,
                },
                status=status.HTTP_201_CREATED,
            )

        return super().create(request, *args, **kwargs)

    @action(
        detail=True, methods=["patch"], permission_classes=[permissions.IsAuthenticated]
    )
    def book(self, request, pk=None):
        """
        建立預約 API
        URL: PATCH /api/appointments/{id}/book/
        """
        appointment = self.get_object()

        if appointment.user is not None:
            return Response(
                {"error": "This slot is already taken."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get week start and end
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday

        # Check if the appointment date is within the current week
        already_booked = (
            Appointment.objects.filter(
                user=request.user,
                date__range=(week_start, week_end),
                status=AppointmentStatus.SCHEDULED,
            )
            .exclude(status=AppointmentStatus.CANCELLED)
            .exists()
        )

        if already_booked:
            return Response(
                {"error": "Quota exceeded. Maximum 1 appointment per week."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.user = request.user
        appointment.status = AppointmentStatus.SCHEDULED
        appointment.reason = request.data.get("reason", "")
        appointment.save()

        email_context = {
            "date": appointment.date,
            "time_slot": appointment.time_slot,
            "student_id": request.user.student_id,
            "reason": appointment.reason,
            "status": appointment.status,
        }

        send_notification_email(
            recipient_email=request.user.email,
            subject=f"[SlotMate] Appointment Scheduled - {appointment.date}",
            context=email_context,
        )

        return Response({"status": "Booked successfully", "id": appointment.id})

    @action(detail=True, methods=["put"], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """
        取消預約 API
        URL: PUT /api/appointments/{id}/cancel/
        """
        appointment = self.get_object()
        if not request.user.is_staff and appointment.user != request.user:
            return Response(
                {"error": "您無權限取消此預約"}, status=status.HTTP_403_FORBIDDEN
            )
        appointment.status = AppointmentStatus.AVAILABLE
        appointment.user = None
        appointment.reason = None
        appointment.save()
        return Response({"status": "已取消預約", "id": appointment.id})

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reschedule(self, request, pk=None):
        """
        修改預約 API
        URL: POST /api/appointments/{old_id}/reschedule/
        """
        old_appointment = self.get_object()
        target_slot_id = request.data.get("target_slot_id")
        new_reason = request.data.get("reason", old_appointment.reason)

        if not target_slot_id:
            return Response(
                {"error": "必須提供目標時段 ID (target_slot_id)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if old_appointment.user != request.user:
            return Response(
                {"error": "您無權限修改此預約"}, status=status.HTTP_403_FORBIDDEN
            )

        if old_appointment.status != AppointmentStatus.SCHEDULED:
            return Response(
                {"error": "只能修改狀態為'已預約'的時段"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target_appointment = Appointment.objects.get(pk=target_slot_id)
        except Appointment.DoesNotExist:
            return Response(
                {"error": "目標時段不存在"}, status=status.HTTP_404_NOT_FOUND
            )
        if (
            target_appointment.status != AppointmentStatus.AVAILABLE
            or target_appointment.user is not None
        ):
            return Response(
                {"error": "目標時段已被預約或不可用"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            old_appointment.user = None
            old_appointment.status = AppointmentStatus.AVAILABLE
            old_appointment.reason = None  # 清空理由
            old_appointment.save()

            target_appointment.user = request.user
            target_appointment.status = AppointmentStatus.SCHEDULED
            target_appointment.reason = new_reason
            target_appointment.save()

        return Response(
            {
                "status": "預約修改成功",
                "old_slot": {
                    "date": old_appointment.date,
                    "time": old_appointment.time_slot,
                },
                "new_slot": {
                    "date": target_appointment.date,
                    "time": target_appointment.time_slot,
                },
            }
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def confirm(self, request, pk=None):
        """
        [Admin Only] 確認預約
        URL: POST /api/appointments/{id}/confirm/
        """
        appointment = self.get_object()

        if appointment.status != AppointmentStatus.SCHEDULED:
            return Response(
                {"error": "只能確認狀態為 '已預約' 的項目"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = AppointmentStatus.CONFIRMED
        appointment.save()

        print(f"DEBUG: 正在確認預約 ID: {appointment.id}")
        if appointment.user:
            print(
                f"DEBUG: 學生: {appointment.user.first_name}, Email: {appointment.user.email}"
            )
        else:
            print("DEBUG: 找不到學生 User 物件")

        # 發送 Email 通知學生
        if appointment.user and appointment.user.email:
            send_confirmation_email(
                recipient_email=appointment.user.email,
                context={
                    "name": appointment.user.first_name,
                    "date": appointment.date,
                    "time_slot": appointment.time_slot,
                    "status": "CONFIRMED",
                },
            )
        else:
            print("DEBUG: ❌ 學生 Email 為空，跳過寄信")

        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """
        [Admin Only] 拒絕/駁回預約
        URL: POST /api/appointments/{id}/reject/
        Body: { "reason": "老師臨時有事" }
        """
        appointment = self.get_object()
        reason = request.data.get("reason")

        if not reason:
            return Response(
                {"error": "駁回預約必須提供理由"}, status=status.HTTP_400_BAD_REQUEST
            )
        if appointment.status not in [
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CONFIRMED,
        ]:
            return Response(
                {"error": "此狀態無法進行駁回操作"}, status=status.HTTP_400_BAD_REQUEST
            )

        user_email = appointment.user.email if appointment.user else None
        user_name = appointment.user.first_name if appointment.user else "Student"

        # 更新狀態
        appointment.status = AppointmentStatus.CANCELLED
        appointment.rejection_reason = reason
        appointment.save()

        # --- Debug 開始 ---
        print(f"DEBUG: 拒絕預約 ID: {appointment.id}, 原因: {reason}")
        print(f"DEBUG: 目標 Email: {user_email}")
        # -----------------

        # 發送 Email 通知
        if user_email:
            send_rejection_email(
                recipient_email=user_email,
                context={
                    "name": user_name,
                    "date": appointment.date,
                    "time_slot": appointment.time_slot,
                    "status": "DECLINED",
                    "reason": reason,
                },
            )
        else:
            print("DEBUG: ❌ 學生 Email 為空，跳過寄信")

        return Response(AppointmentSerializer(appointment).data)

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def admin_list(self, request):
        """
        [Admin Only] 取得特定格式的後台列表
        支援日期範圍篩選
        URL: GET /api/appointments/admin_list/?start_date=2026-01-01&end_date=2026-01-31
        """
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        queryset = self.get_queryset()

        # 日期範圍篩選邏輯
        if start_date and end_date:
            # 搜尋這段時間內的預約
            queryset = queryset.filter(date__range=[start_date, end_date])
        elif start_date:
            # 如果只給開始日期
            # 搜尋這天之後的
            queryset = queryset.filter(date__gte=start_date)
        elif end_date:
            # 如果只給結束日期
            # 搜尋這天之前的
            queryset = queryset.filter(date__lte=end_date)

        # 加入排序：日期(新到舊)、時間(早到晚)
        queryset = queryset.order_by("-date", "time_slot")

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AvailableSlotsView(APIView):
    """
    回傳所有狀態為 AVAILABLE 的時段
    """

    permission_classes = [AllowAny]

    def get(self, request):

        available_appointments = Appointment.objects.filter(
            status=AppointmentStatus.AVAILABLE
        ).order_by("date", "time_slot")

        data = {}
        for appt in available_appointments:
            date_str = str(appt.date)
            if date_str not in data:
                data[date_str] = []
            data[date_str].append(appt.time_slot)

        return Response(data)
