import base64
import hashlib
import hmac
import json
import time

SECRET_KEY = b"change-me"
HEADER = {"alg": "HS256", "typ": "JWT"}


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def _sign(message: str) -> bytes:
    return hmac.new(SECRET_KEY, message.encode(), hashlib.sha256).digest()


def make_token(username, role, ttl_seconds=3600):
    payload = {"username": username, "role": role, "exp": int(time.time()) + ttl_seconds}
    header_part = _b64encode(json.dumps(HEADER).encode())
    payload_part = _b64encode(json.dumps(payload).encode())
    message = f"{header_part}.{payload_part}"
    signature = _b64encode(_sign(message))
    return f"{message}.{signature}"


def verify_token(token: str):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_part, payload_part, sig_part = parts
        message = f"{header_part}.{payload_part}"
        expected_sig = _b64encode(_sign(message))
        if not hmac.compare_digest(expected_sig, sig_part):
            return None
        payload_json = _b64decode(payload_part).decode()
        payload = json.loads(payload_json)
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None
