import secrets
import string


class OTPGenerator:
    """
    產生高強度的數字 OTP 驗證碼。
    內建多重驗證規則，防止產生過於簡單或連續的數字組合。
    """

    def __init__(self, length=6, max_retries=100):
        self._length = length
        self._max_retries = max_retries
        self._digits_pool = string.digits

    def generate(self) -> str:
        """
        [Public] 產生符合安全規則的 OTP
        """
        for _ in range(self._max_retries):
            candidate = self._generate_candidate()
            if self._validate_candidate(candidate):
                return candidate
        return candidate

    def _generate_candidate(self) -> str:
        """
        [Private] 使用加密安全的 secrets 產生隨機數字字串
        """
        return "".join(secrets.choice(self._digits_pool) for _ in range(self._length))

    def _validate_candidate(self, otp: str) -> bool:
        """
        [Private] 總驗證入口
        """
        if self._is_all_same(otp):
            return False
        if self._is_sequential(otp):
            return False
        if self._is_simple_pattern(otp):
            return False
        if not self._has_enough_unique_digits(otp):
            return False
        return True

    def _is_all_same(self, otp: str) -> bool:
        """
        [Private] 檢查是否全部數字都相同 (例如: 111111)
        """
        return len(set(otp)) == 1

    def _is_sequential(self, otp: str) -> bool:
        """
        [Private] 檢查是否為連續數字 (例如: 123456 或 654321)
        """
        forward_seq = "0123456789"
        backward_seq = "9876543210"
        return otp in forward_seq or otp in backward_seq

    def _is_simple_pattern(self, otp: str) -> bool:
        """
        [Private] 檢查是否為簡單重複模式 (例如: 121212, 101010)
        """
        # 檢查前兩碼是否重複出現了3次 (針對 6 碼 OTP)
        if self._length == 6:
            pattern = otp[:2]
            if pattern * 3 == otp:
                return True
        return False

    def _has_enough_unique_digits(self, otp: str) -> bool:
        """
        [Private] 檢查不重複的數字是否足夠多 (至少要有 3 種不同數字)
        例如: 112211 (只有1,2) -> False
        """
        return len(set(otp)) >= 3
