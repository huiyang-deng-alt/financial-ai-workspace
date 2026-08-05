import hashlib
import hmac
import secrets
import time

import jwt
SECRET_KEY = "dev-secret-change-me"
ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 3600


def hash_password(password: str) -> str:

    salt = secrets.token_hex(16)
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100_000,
    )
    return f"{salt}${hash_bytes.hex()}"

def verify_password(password: str, stored: str) -> bool:
    salt, expected = stored.split('$')
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100_000,
    )
    return hmac.compare_digest(hash_bytes.hex(), expected)

def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

if __name__ == "__main__":
    # 自测：直接运行本文件验证
    pwd_hash = hash_password("test123")
    print("hash:", pwd_hash)
    assert verify_password("test123", pwd_hash), "正确密码应通过"
    assert not verify_password("wrong", pwd_hash), "错误密码应失败"

    token = create_token(42)
    print("token:", token[:50], "...")
    parts = token.split(".")
    assert len(parts) == 3, "JWT 必须是三段"
    payload = decode_token(token)
    assert payload["sub"] == "42", "payload 应包含用户 id"
    print("[OK] 4 个函数全部通过")