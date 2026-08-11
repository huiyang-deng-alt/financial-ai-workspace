"""金融顾问 AI 工作台 —— 集成后端（认证 + RAG 问答 + 查询改写 + 对话历史）

合并 api.py（RAG 问答）+ auth_api_db.py（JWT 认证/历史）+ 查询改写（W5 D1）：
前端统一连这个后端，流程 = 注册 → 登录 → 带 token 提问（省略句自动改写）→ 查历史
"""
import os
from pathlib import Path

# ============ 1. 环境 ============
os.chdir(Path(__file__).resolve().parent)          # 切到 rag_system 目录（向量库 chroma_db 在这里）
os.environ["HF_HOME"] = str(Path(".hf_cache").resolve())
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import auth
import db
from src.rag_pipeline import RAGPipeline

# ============ 2. 应用 ============
app = FastAPI(title="金融顾问 AI 工作台")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ============ 3. 初始化 ============
db.init_db()
pipeline = RAGPipeline(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    db_path="./chroma_db",
    collection_name="my_knowledge_base",
)

# ============ 4. 认证依赖 ============
security = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """校验 token → 返回当前用户 id；失败抛 401"""
    try:
        payload = auth.decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="token 无效或已过期")
    return int(payload["sub"])

# ============ 5. 查询改写（W5 D1 新学） ============
def rewrite_query(question: str, history: list, llm_client) -> str:
    """省略句 → 完整问题：结合最近 3 轮历史，让检索器知道'那/它'指什么"""
    if not history:                    # 没有历史 → 不用改写
        return question

    history_text = "\n".join(
        f"用户：{h['question']}\n助手：{h['answer']}" for h in history[-3:]
    )

    prompt = f"""以下是对话历史：
{history_text}

用户的最新问题是：{question}

请把这个问题改写成一条【独立、完整、不依赖前文】的提问，只输出改写结果。如果问题已经完整，直接原样输出。"""

    resp = llm_client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0               # 改写要确定性，不许发挥
    )
    return resp.choices[0].message.content.strip()

# ============ 6. 请求体（Pydantic） ============
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    question: str

# ============ 7. 接口 ============
@app.post("/register")
def register(req: RegisterRequest):
    """注册：哈希密码 → 写库"""
    user_id = db.create_user(req.username, auth.hash_password(req.password))
    if user_id is None:  # UNIQUE 约束触发 → 用户名重复
        raise HTTPException(status_code=400, detail="用户名已存在")
    return {"message": "注册成功", "username": req.username}

@app.post("/login")
def login(req: LoginRequest):
    """登录：验密码 → 签发 JWT"""
    user = db.get_user_by_username(req.username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not auth.verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = auth.create_token(user["id"])
    return {"token": token, "token_type": "bearer"}

@app.post("/chat")
def chat(req: ChatRequest, user_id: int = Depends(get_current_user_id)):
    """带认证的 RAG 问答：验 token → 查询改写 → 检索生成 → 存历史"""
    # 1. 取该用户最近 3 轮历史（用于改写）
    history = db.get_messages_by_user(user_id)[-3:]

    # 2. 查询改写：'那净利润呢' → '宁德时代2025年净利润是多少'
    question = rewrite_query(req.question, history, pipeline.llm_client)
    print(f"[改写] {req.question!r} -> {question!r}")

    # 3. 检索生成（用改写后的完整问题）
    result = pipeline.query(question, top_k=3)
    answer = result["answer"]
    sources = result.get("sources", [])

    # 4. 存历史：存原始问题（历史里显示用户真正说的，而不是改写后的）
    db.save_message(user_id, req.question, answer)
    return {"answer": answer, "sources": sources}

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

@app.get("/me")
def me(user_id: int = Depends(get_current_user_id)):
    """验证身份：返回当前用户信息"""
    row = db.get_user_by_id(user_id)
    if row is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return {"user_id": row["id"], "username": row["username"]}

@app.get("/")
def root():
    return {"message": "金融顾问 AI 工作台 API", "chunks": pipeline.get_stats()["total_chunks"]}