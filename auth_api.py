"""用户认证 API（JWT 三接口）—— 学习版：完整代码 + 逐行注释

学习流程：
1. 先读注释，看懂 3 个接口 + Depends 依赖注入
2. 直接运行本文件自测，看到 [OK] 全部通过
3. 在 auth_api_practice.py 里自己重写一遍（不看本文件）
"""

# ============ 第 1 部分：import ============
from fastapi import FastAPI, Depends, HTTPException
#   Depends      ：依赖注入，FastAPI 的核心魔法（第 5 部分细讲）
#   HTTPException：主动抛错误，让接口返回给客户端明确的错误信息
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
#   HTTPBearer：FastAPI 内置的"从请求头里取 token"的工具
from pydantic import BaseModel
#   BaseModel：数据校验，自动把请求的 JSON 转成 Python 对象
import auth
#   复用我们刚学的 4 个函数：hash_password / verify_password / create_token / decode_token

# ============ 第 2 部分：应用与"数据库" ============
app = FastAPI(title="用户系统")
# 创建 FastAPI 应用，后面 uvicorn 启动的就是它

# 内存用户表（学习用）：{用户名: {user_id: 数字, password_hash: 字符串}}
# 缺点：程序一重启，数据就没了。8/15 冲刺会换成 SQLite 持久化
users_db = {}
next_user_id = 1  # 自增编号：第一个注册的用户 id=1

# ============ 第 3 部分：请求体模型（Pydantic） ============
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

# BaseModel 的作用：FastAPI 收到 JSON 后自动做两件事
# · 缺字段 / 类型不对 → 直接返回 422 错误，不用你手写判断
# · 校验通过 → req.username / req.password 就是干净的数据

# ============ 第 4 部分：三个接口 ============
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
        # ② 重算哈希对比。注意：用户名不存在和密码错误，
        #    返回的话术故意一模一样，防止攻击者猜出"这个用户名是否存在"
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = auth.create_token(user["user_id"])   # ③ 验证通过 → 签发 JWT
    return {"token": token, "token_type": "bearer"}

# ============ 第 5 部分：依赖注入（Depends） ============
security = HTTPBearer()
# HTTPBearer 负责检查请求头里的 Authorization: Bearer <token>
# 客户端每次访问 /me 都要带这个头；不带 → HTTPBearer 直接返回 403

@app.get("/me")
def me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """查看当前登录用户：前端带 token 来，后端验完身份后告诉你是谁"""
    token = credentials.credentials              # ① 从请求头里取出 token 字符串
    try:
        payload = auth.decode_token(token)       # ② 验签名 + 验过期，通过则拿到 payload
    except Exception:                            #    签名错 / 过期 / 格式错都会抛异常
        raise HTTPException(status_code=401, detail="token 无效或已过期")
    # ③ 用 token 里的 user_id 反查用户名（循环遍历内存表）
    username = None
    for name, u in users_db.items():
        if u["user_id"] == int(payload["sub"]):
            username = name
            break
    if username is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return {"user_id": payload["sub"], "username": username}

# ============ 第 6 部分：自测（用代码代替浏览器测接口） ============
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