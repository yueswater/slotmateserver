import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from notify_letter.utils import send_password_reset_email
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from utils.network import get_client_ip
from utils.otp_generator import OTPGenerator

from .serializers import (
    ActivateAccountSerializer,
    ChangePasswordSerializer,
    CheckStudentSerializer,
    ForgotPasswordSerializer,
    PasswordResetConfirmSerializer,
    TokenObtainPairSerializer,
)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            serializer = self.get_serializer(data=request.data)
            User = get_user_model()
            user_id = request.data.get("student_id") or request.data.get("username")
            if user_id:
                try:
                    user = User.objects.get(student_id=user_id)
                    user.last_login_ip = get_client_ip(request)
                    update_last_login(None, user)
                    user.save()
                except User.DoesNotExist:
                    pass
        return response


class CheckStudentView(APIView):
    permission_classes = [AllowAny]
    serializer_class = CheckStudentSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            return Response(
                {
                    "message": "Student ID verified, please set your password",
                    "valid": True,
                },
                status=status.HTTP_200_OK,
            )
        error_msg = next(iter(serializer.errors.values()))[0]
        return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ActivateAccountSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Account activated successfully, please log in"},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.last_logout = timezone.now()
            request.user.save()
            return Response({"message": "成功登出"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.is_first_login = False
            user.save()

            return Response(
                {"message": "密碼修改成功，請重新登入"}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "student_id": user.student_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "department": user.department,
                "grade": user.grade,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "last_login": user.last_login,
                "last_login_ip": getattr(user, "last_login_ip", None),
            },
            status=status.HTTP_200_OK,
        )


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            student_id = serializer.validated_data["student_id"]
            user = get_user_model().objects.get(student_id=student_id)

            otp = OTPGenerator(length=6).generate()
            cache.set(f"password_reset_otp_{user.id}", otp, timeout=600)

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            frontend_url = getattr(
                settings, "FRONTEND_URL", "https://slotmate.yueswater.com"
            )
            reset_link = f"{frontend_url}/reset-password/{uid}/{token}"

            try:
                send_password_reset_email(
                    user.email,
                    {
                        "user": user,
                        "otp": otp,
                        "reset_link": reset_link,
                        "year": datetime.datetime.now().year,
                    },
                )
            except Exception as e:
                return Response(
                    {"error": "Failed to send email."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {"message": "Password reset email sent.", "email": user.email},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password has been reset successfully."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
