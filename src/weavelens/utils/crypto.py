from __future__ import annotations
from typing import Optional
from cryptography.fernet import Fernet

def get_fernet(key: Optional[str]) -> Optional[Fernet]:
    if not key: return None
    return Fernet(key.encode() if isinstance(key, str) else key)

def maybe_encrypt(text: str, key: Optional[str]) -> str:
    f = get_fernet(key)
    if not f: return text
    return "enc:" + f.encrypt(text.encode()).decode()

def maybe_decrypt(text: str, key: Optional[str]) -> str:
    if not text.startswith("enc:"): return text
    f = get_fernet(key)
    if not f: return text
    token = text[4:].encode()
    return f.decrypt(token).decode()
