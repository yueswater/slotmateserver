import re

from rest_framework import serializers


class PasswordStrengthValidator:
    def __call__(self, value, user=None):
        # 長度檢查
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )

        # 混合字元檢查
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )
        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )
        if not re.search(r"\d", value):
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError(
                "Password must contain at least one symbol."
            )

        if user:
            # 避免包含帳號
            if user.student_id and user.student_id in value:
                raise serializers.ValidationError(
                    "Password cannot contain your Student ID."
                )

        # 避免重複字元
        if re.search(r"(.)\1\1", value):
            raise serializers.ValidationError(
                "Avoid using repeating characters (e.g., 'aaa')."
            )

        # 避免連續字元
        sequences = [
            "abc",
            "bcd",
            "cde",
            "def",
            "efg",
            "fgh",
            "ghi",
            "hij",
            "ijk",
            "jkl",
            "klm",
            "lmn",
            "mno",
            "nop",
            "opq",
            "pqr",
            "qrs",
            "rst",
            "stu",
            "tuv",
            "uvw",
            "vwx",
            "wxy",
            "xyz",
            "123",
            "234",
            "345",
            "456",
            "567",
            "678",
            "789",
        ]
        if any(seq in value.lower() for seq in sequences):
            raise serializers.ValidationError(
                "Avoid using sequential characters (e.g., 'abc', '123')."
            )

        return value
