from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import auth

app = FastAPI(title="用户系统")
users_db = {}
next_user_id = 1
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(req: RegisterRequest):
    """注册：用户名+密码 → 密码哈希后存进 users_db"""
    if req.username in users_db:                 # ① 用户名重复，直接拒绝
        raise HTTPException(status_code=400, detail="用户名已存在")
    global next_user_id                          # ② 要改全局变量，必须声明 global
    users_db[req.username] = {                   # ③ 只存哈希，绝不存明文密码
        "user_id": next_user_id,
        "password_hash": auth.hash_password(req.password),
    }
    next_user_id += 1
    return {"message": "注册成功", "username": req.username}

@app.post("/login")
def login(req: LoginRequest):
    """登录：验证密码 → 通过则签发 JWT"""
    user = users_db.get(req.username)            # ① 查用户；不存在时 .get 返回 None
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not auth.verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = auth.create_token(user["user_id"])   # ③ 验证通过 → 签发 JWT
    return {"token": token, "token_type": "bearer"}
security = HTTPBearer()
@app.get("/me")
def me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = auth.decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="token 无效或已过期")
    username = None
    for name, u in users_db.items():
        if u["user_id"] == int(payload["sub"]):
            username = name
            break
    if username is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return {"user_id": payload["sub"], "username": username}
if __name__ == "__main__":
    # TestClient：模拟一个客户端发请求，不用真的开服务器
    from fastapi.testclient import TestClient
    client = TestClient(app)

    # 1. 正常注册
    r = client.post("/register", json={"username": "dhy", "password": "test123"})
    assert r.status_code == 200, r.text
    print("[1/5] 注册 OK:", r.json())

    # 2. 重复注册应被拒绝（400）
    r = client.post("/register", json={"username": "dhy", "password": "test123"})
    assert r.status_code == 400, r.text
    print("[2/5] 重复注册被拒绝 OK")

    # 3. 登录拿 token
    r = client.post("/login", json={"username": "dhy", "password": "test123"})
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    print("[3/5] 登录拿到 token OK:", token[:30], "...")

    # 4. 带 token 访问 /me，能拿到身份
    r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    print("[4/5] /me 身份验证 OK:", r.json())

    # 5. 不带 token 访问 /me 应被拒绝（401/403）
    r = client.get("/me")
    assert r.status_code in (401, 403), r.text
    print("[5/5] 无 token 被拒绝 OK")

    print("\n[OK] 全部通过")