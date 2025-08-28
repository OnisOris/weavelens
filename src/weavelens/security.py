from __future__ import annotations
import time, hmac, hashlib, base64
from typing import Optional

# простейший JWT (HS256) без сторонних зависимостей
def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _b64url_json(obj: dict) -> str:
    import json
    return _b64url(json.dumps(obj, separators=(',', ':')).encode())

def _sign(msg: bytes, secret: str) -> str:
    return _b64url(hmac.new(secret.encode(), msg, hashlib.sha256).digest())

def jwt_encode(payload: dict, secret: str, exp_seconds: int = 3600) -> str:
    header = {"alg":"HS256","typ":"JWT"}
    payload = {**payload, "exp": int(time.time()) + exp_seconds}
    header_b64 = _b64url_json(header)
    payload_b64 = _b64url_json(payload)
    sig = _sign(f"{header_b64}.{payload_b64}".encode(), secret)
    return f"{header_b64}.{payload_b64}.{sig}"

def jwt_decode(token: str, secret: str) -> Optional[dict]:
    try:
        header_b64, payload_b64, sig = token.split(".")
        expected = _sign(f"{header_b64}.{payload_b64}".encode(), secret)
        if not hmac.compare_digest(expected, sig):
            return None
        import json, base64
        def b64d(s: str) -> bytes:
            s += "=" * (-len(s) % 4)
            return base64.urlsafe_b64decode(s.encode())
        payload = json.loads(b64d(payload_b64))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None
