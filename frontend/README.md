# Enterprise AI Workspace

> 一个基于 DeepSeek 的金融类顾问 AI 工作台，支持 RAG 知识库检索、用户认证和智能问答。

## 技术栈

| 层 | 技术 |
|------|------|
| 后端 | FastAPI（Python） |
| AI | DeepSeek API + RAG（检索增强生成） |
| 向量数据库 | ChromaDB + SentenceTransformer（all-MiniLM-L6-v2，父子分块检索） |
| 前端 | Streamlit |
| 认证 | JWT（注册 / 登录 / 身份验证） |
| 数据库 | SQLite（对话历史规划中） |

## 当前功能

- [x] Streamlit ChatBot 对话界面
- [x] FastAPI 后端（路由 + Pydantic 校验 + 依赖注入 + CORS）
- [x] RAG 知识库：PDF/Word/HTML/TXT 加载 → 父子分块（子块 200 字检索 + 父块 1500 字喂 LLM）→ 向量化 → 检索 → LLM 生成
- [x] 中英文跨语言查询（DeepSeek 查询翻译）
- [x] JWT 用户认证（密码哈希 + /register /login /me）
- [ ] RAG 检索质量优化（多语言 Embedding，当前内容级命中 22.2%，见 `4.RAG/评估记录.md`）
- [ ] Agent 系统：Tool Calling + Workflow（Week 7-9）
- [ ] Docker 部署 + 线上 URL（Week 6-7）

## 本地运行

```bash
# 前端（终端 1）
cd "Enterprise AI Workspace"
streamlit run src/app.py

# 后端（终端 2，进入 rag_system 目录）
cd 4.RAG/rag_system
.\.venv\Scripts\python.exe -m uvicorn api:app --reload

# RAG 交互入口（终端 3，可选）
cd 4.RAG/rag_system
.\.venv\Scripts\python.exe main.py
```

## 项目结构

```
AI应用开发教程/
├── Enterprise AI Workspace/        # 前端 + 项目文档
│   ├── src/
│   │   └── app.py                  # Streamlit ChatBot 前端
│   ├── README.md
│   ├── .env.example
│   ├── .gitignore
│   ├── requirements.txt
│   └── 踩坑记录.md
└── 4.RAG/rag_system/               # RAG 后端子系统
    ├── api.py                      # FastAPI 入口（RAG API 壳）
    ├── main.py                     # RAG 命令行交互入口
    ├── auth.py                     # JWT 认证模块（哈希 + 签发/验证）
    ├── auth_api.py                 # 认证接口教学版（/register /login /me）
    ├── src/
    │   ├── document_loader.py      # 文档加载（PDF/Word/HTML/TXT）
    │   ├── text_processor.py       # 文本清洗 + 父子分块（200/1500）
    │   ├── vector_store.py         # 向量存储（ChromaDB + SentenceTransformer）
    │   ├── retriever.py            # 检索（翻译 + 向量检索 + 父块返回）+ LLM 生成
    │   └── rag_pipeline.py         # 完整 RAG 流水线
    ├── data/                       # 知识库文档（财报/政策 PDF）
    ├── chroma_db/                  # 向量数据库（本地数据，不提交 Git）
    ├── .hf_cache/                  # HuggingFace 模型缓存（不提交 Git）
    └── .env                        # 真实环境变量（不提交 Git）
```

## 作者

- 广州理工学院 · 人工智能专业
- 学习路线：AI 应用开发工程师（Python + SQL + RAG + Agent）