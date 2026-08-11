
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
import db
import time
#   time：计算请求耗时
from fastapi.middleware.cors import CORSMiddleware
# ============ 第 2 部分：应用与"数据库" ============
app = FastAPI(title="用户系统")
# 创建 FastAPI 应用，后面 uvicorn 启动的就是它
# ============ 中间件（8/5 新学） ============
# 写法 B：CORS 跨域（现成中间件，配置参数即可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 允许所有来源（生产环境写具体前端地址）
    allow_methods=["*"],      # 允许所有 HTTP 方法
    allow_headers=["*"],      # 允许所有请求头（含 Authorization）
)

# 写法 A：请求日志中间件（自定义逻辑，记录每个请求的方法/路径/耗时）
@app.middleware("http")
async def log_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    print(f"[日志] {request.method} {request.url.path} 耗时 {duration:.3f}s")
    return response

# 内存用户表（学习用）：{用户名: {user_id: 数字, password_hash: 字符串}}
# 缺点：程序一重启，数据就没了。8/15 冲刺会换成 SQLite 持久化
db.init_db()

# ============ 第 3 部分：请求体模型（Pydantic） ============
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    question: str
    answer: str

# BaseModel 的作用：FastAPI 收到 JSON 后自动做两件事
# · 缺字段 / 类型不对 → 直接返回 422 错误，不用你手写判断
# · 校验通过 → req.username / req.password 就是干净的数据

# ============ 第 4 部分：三个接口 ============
@app.post("/register")
def register(req: RegisterRequest):
    """注册：用户名+密码 → 密码哈希后存进 users_db"""
    user_id = db.create_user(req.username, auth.hash_password(req.password))
    if user_id is None:  # UNIQUE 约束触发 → 用户名重复
        raise HTTPException(status_code=400, detail="用户名已存在")
    return {"message": "注册成功", "username": req.username}

@app.post("/login")
def login(req: LoginRequest):
    """登录：验证密码 → 通过则签发 JWT"""
    user = db.get_user_by_username(req.username)           # ① 查用户；不存在时 .get 返回 None
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not auth.verify_password(req.password, user["password_hash"]):
        # ② 重算哈希对比。注意：用户名不存在和密码错误，
        #    返回的话术故意一模一样，防止攻击者猜出"这个用户名是否存在"
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = auth.create_token(user["id"])   # ③ 验证通过 → 签发 JWT
    return {"token": token, "token_type": "bearer"}

# ============ 第 5 部分：依赖注入（Depends） ============
security = HTTPBearer()
def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """公共逻辑：校验 token → 返回当前登录用户 id；失败抛 401"""
    try:
        payload = auth.decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="token 无效或已过期")
    return int(payload["sub"])
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
    row = db.get_user_by_id(int(payload["sub"]))
    if row is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    username = row["username"]
    return {"user_id": payload["sub"], "username": username}

@app.post("/chat/save")
def save_chat(req: ChatRequest, user_id: int = Depends(get_current_user_id)):
    """存一轮问答到对话历史（需登录）"""
    msg_id = db.save_message(user_id, req.question, req.answer)
    return {"message": "已保存", "id": msg_id}

@app.get("/history")
def get_history(user_id: int = Depends(get_current_user_id)):
    """查当前用户的对话历史（需登录）"""
    rows = db.get_messages_by_user(user_id)
    return {
        "count": len(rows),
        "messages": [
            {"id": r["id"], "question": r["question"], "answer": r["answer"], "created_at": r["created_at"]}
            for r in rows
        ],
    }

@app.get("/users")
def list_users():
    items = [{"id": u["id"], "username": u["username"]} for u in users_db.values()]
    return {"total": len(items), "items": items}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"id": user["id"], "username": user["username"]}

@app.post("/users", status_code=201)
def create_user(req: UserCreate):
    global next_id
    for u in users_db.values():
        if u["username"] == req.username:
            raise HTTPException(status_code=400, detail="用户名已存在")
    user = {"id": next_id, "username": req.username, "password_hash": req.password}
    users_db[next_id] = user
    next_id += 1
    return {"id": user["id"], "username": user["username"]}

@app.put("/users/{user_id}")
def update_user(user_id: int, req: UserUpdate):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="用户不存在")
    users_db[user_id]["username"] = req.username
    users_db[user_id]["password_hash"] = req.password
    return {"id": user_id, "username": req.username}

@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="用户不存在")
    del users_db[user_id]
    return None
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

    # 6. 登录后存两条对话
    r = client.post("/chat/save", headers={"Authorization": f"Bearer {token}"},
                    json={"question": "宁德时代2025年营收多少？", "answer": "约3620亿元"})
    assert r.status_code == 200, r.text
    r = client.post("/chat/save", headers={"Authorization": f"Bearer {token}"},
                    json={"question": "货币政策是什么基调？", "answer": "适度宽松"})
    assert r.status_code == 200, r.text
    print("[6/8] 存对话 OK")

    # 7. 查历史，应该看到 2 条
    r = client.get("/history", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["count"] == 2, data
    print("[7/8] 查历史 OK，共", data["count"], "条")

    # 8. 不带 token 查历史应被拒绝
    r = client.get("/history")
    assert r.status_code in (401, 403), r.text
    print("[8/8] 无 token 查历史被拒绝 OK")

    print("\n[OK] 全部通过")