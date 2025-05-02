from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from datetime import timedelta

class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    """
    Override Django's default password reset token generator
    to expire tokens after 10 minutes.
    """
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp) + str(user.is_active)

    def check_token(self, user, token):
        # Call parent check_token
        if not super().check_token(user, token):
            return False
        ts_b36, _ = token.split("-")
        ts_int = int(ts_b36, 36)

        token_created_time = self._num_seconds(self._today()) - (ts_int * self.TIME_STEP)
        now = self._num_seconds(timezone.now())

        elapsed_time = now - token_created_time

        if elapsed_time > 600: 
            return False

        return True

custom_password_reset_token = CustomPasswordResetTokenGenerator()
