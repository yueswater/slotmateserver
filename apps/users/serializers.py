import re

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from users.validator import PasswordStrengthValidator

from .models import AllowedStudent, User


class TokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "student_id": self.user.student_id,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
            "name": f"{self.user.last_name}{self.user.first_name}",
            "is_staff": self.user.is_staff,
            "is_superuser": self.user.is_superuser,
            "is_first_login": self.user.is_first_login,
        }
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct.")
        return value

    def validate(self, data):
        user = self.context["request"].user
        new_pwd = data.get("new_password")
        confirm_pwd = data.get("confirm_password")
        print(new_pwd, confirm_pwd)

        # Basic consistency check
        if new_pwd != confirm_pwd:
            raise serializers.ValidationError(
                {"confirm_password": "New passwords do not match."}
            )

        validator = PasswordStrengthValidator()
        validator(new_pwd, user=user)

        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["student_id", "email", "first_name", "last_name", "password"]

    def validate_student_id(self, value):
        # 檢查學號是否已註冊
        if User.objects.filter(student_id=value).exists():
            raise serializers.ValidationError("此學號已註冊")
        # 檢查學號是否在允許註冊名單中
        if not AllowedStudent.objects.filter(student_id=value).exists():
            raise serializers.ValidationError("此學號不在允許註冊名單中，請聯繫老師")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "student_id",
            "first_name",
            "last_name",
            "department",
            "grade",
            "email",
        ]


class CheckStudentSerializer(serializers.Serializer):
    student_id = serializers.CharField(required=True)

    def validate_student_id(self, value):
        try:
            user = User.objects.get(student_id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "Student ID is not in our records. Failed to activate."
            )

        if not getattr(user, "is_first_login", True):
            raise serializers.ValidationError(
                "This account has already been activated. Please log in directly."
            )

        return value


class ActivateAccountSerializer(serializers.Serializer):
    student_id = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        error_messages={
            "invalid": "Please provide a valid email address.",
            "blank": "Email cannot be blank",
        },
    )

    def validate_student_id(self, value):
        try:
            user = User.objects.get(student_id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("ID not found.")

        if not getattr(user, "is_first_login", True):
            raise serializers.ValidationError("Account already activated.")

        return value

    def save(self):
        student_id = self.validated_data["student_id"]
        password = self.validated_data["password"]
        email = self.validated_data.get("email")

        user = User.objects.get(student_id=student_id)
        user.set_password(password)

        if email:
            user.email = email

        user.is_first_login = False
        user.is_active = True
        user.save()
        return user
