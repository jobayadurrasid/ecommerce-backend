import bcrypt
import hashlib
import base64

def hash_password(password: str) -> str:
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    prehashed = base64.b64encode(digest)  # 44 bytes, always under 72
    return bcrypt.hashpw(prehashed, bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    prehashed = base64.b64encode(digest)
    return bcrypt.checkpw(prehashed, hashed.encode())   