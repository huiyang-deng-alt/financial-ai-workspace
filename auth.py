"""用户认证模块（JWT）—— 学习版：完整代码 + 逐行注释

学习流程：
1. 逐行读注释，把 4 个函数看懂
2. 运行本文件，看到 [OK] 4 个函数全部通过
3. 自己动手在新建的 auth_practice.py 里重敲一遍（不看本文件）
4. 明天 L1 练习：把关键行挖掉让你填
"""
import hashlib
import hmac
import secrets
import time

import jwt

SECRET_KEY = "dev-secret-change-me"  # 生产环境放 .env，不能硬编码
ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 3600  # token 有效期 1 小时


def hash_password(password: str) -> str:
    """密码哈希：加盐 + PBKDF2，返回 '盐$哈希'。"""
    # ① secrets.token_hex(16)：生成随机盐（16 字节 → 32 个十六进制字符）
    #   secrets 是"安全随机"库，比 random 更难预测，密码场景必须用它
    salt = secrets.token_hex(16)
    # ② pbkdf2_hmac：把"密码+盐"迭代 10 万次，得到一个固定长度字节串
    #   · 'sha256'：哈希算法
    #   · password.encode('utf-8')：哈希算法只吃字节，字符串要先转字节
    #   · salt.encode('utf-8')：盐同样转字节
    #   · 100_000：迭代次数，越大越难被暴力破解（但也越慢）
    #   为什么"慢"是好事：攻击者破解一个密码，也要重算 10 万次
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100_000,
    )
    # ③ 盐和哈希用 $ 拼起来存，验证时能拆开（$ 是分隔符）
    return f"{salt}${hash_bytes.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """校验密码：拆出盐 → 用相同参数重算 → 恒定时长比较。"""
    # ① 拆开 '盐$哈希'
    salt, expected = stored.split('$')
    # ② 用和 hash_password 完全一样的参数重算（算法/编码/迭代次数必须一致）
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100_000,
    )
    # ③ hmac.compare_digest：恒定时长比较
    #   普通 == 在第一个不同字节就返回，攻击者可利用时间差猜密码；
    #   compare_digest 无论对错耗时都一样，防"时序攻击"
    return hmac.compare_digest(hash_bytes.hex(), expected)


def create_token(user_id: int) -> str:
    """签发 JWT：把身份信息放进 payload，签上服务器密钥。"""
    payload = {
        "sub": str(user_id),  # subject：标识"你是谁"，规范要求字符串
        "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS,  # 过期时间戳（秒）
    }
    # jwt.encode 帮你完成整个流程：
    #   base64(header) + "." + base64(payload) + "." + HMAC-SHA256(前两段, 密钥)
    # 返回一串字符串，就是客户端要保存的 token
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """验证并解析 JWT。jwt.decode 内部做三件事：
    1. 验签名：密钥对不上 → 抛 InvalidSignatureError
    2. 验过期：exp 过了 → 抛 ExpiredSignatureError
    3. 通过则返回 payload 字典
    """
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