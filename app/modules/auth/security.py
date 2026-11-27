import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict
from app.core.config import get_settings


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def create_access_token(user_id: int, role: str, email: str) -> str:
    settings = get_settings()
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "role": role,
        "email": email,
        "iat": now,
        "exp": now + settings.JWT_EXPIRE_MINUTES * 60,
    }
    h_seg = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p_seg = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{h_seg}.{p_seg}".encode("ascii")
    sig = hmac.new(settings.JWT_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{h_seg}.{p_seg}.{_b64url_encode(sig)}"


def decode_access_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Token JWT inválido")
    h_seg, p_seg, sig_seg = parts
    signing_input = f"{h_seg}.{p_seg}".encode("ascii")
    expected_sig = hmac.new(settings.JWT_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url_decode(sig_seg), expected_sig):
        raise ValueError("Firma JWT inválida")
    payload = json.loads(_b64url_decode(p_seg).decode("utf-8"))
    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("Token JWT expirado")
    return payload
