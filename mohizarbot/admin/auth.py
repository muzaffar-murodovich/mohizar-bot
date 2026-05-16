from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass


@dataclass
class AuthData:
    user_id: int
    first_name: str = ""
    username: str = ""
    photo_url: str = ""


class TelegramLoginVerifier:
    def __init__(self, bot_token: str, max_age_seconds: int = 86400) -> None:
        self._secret = hashlib.sha256(bot_token.encode()).digest()
        self._max_age = max_age_seconds

    def verify(self, data: dict[str, str]) -> AuthData | None:
        received_hash = data.get("hash", "")
        if not received_hash:
            return None

        # Verify auth_date freshness
        auth_date_str = data.get("auth_date", "0")
        try:
            auth_date = int(auth_date_str)
        except ValueError:
            return None

        if time.time() - auth_date > self._max_age:
            return None

        # Build data check string per Telegram spec
        check_pairs = sorted((k, v) for k, v in data.items() if k != "hash")
        check_string = "\n".join(f"{k}={v}" for k, v in check_pairs)

        computed = hmac.digest(self._secret, check_string.encode(), hashlib.sha256).hex()

        if not hmac.compare_digest(computed, received_hash):
            return None

        return AuthData(
            user_id=int(data.get("id", "0")),
            first_name=data.get("first_name", ""),
            username=data.get("username", ""),
            photo_url=data.get("photo_url", ""),
        )
