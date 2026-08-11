# 金融顾问 AI 工作台（rag_system）

> 基于 DeepSeek 的金融类顾问 AI 后端系统：RAG 知识库问答 + JWT 用户认证 + 对话历史 + 混合检索。
> 广州理工学院 · 人工智能专业 · AI 应用开发方向学习项目

## 技术栈

| 层 | 技术 |
|------|------|
| 后端 | FastAPI（Python） |
| AI | DeepSeek API + RAG（检索增强生成） |
| 向量检索 | ChromaDB + SentenceTransformer（all-MiniLM-L6-v2）+ **混合检索（BM25+jieba + 向量 + RRF）** |
| 认证 | JWT（密码哈希 + 注册 / 登录 / 身份验证） |
| 数据库 | SQLite（用户表 + 对话历史） |
| 中间件 | 请求日志 + CORS |

## 当前功能

- [x] RAG 知识库：PDF 加载 → 父子分块（子块 200 字检索 + 父块 1500 字喂 LLM）→ 向量化 → 检索 → LLM 生成
- [x] 中英文跨语言查询（DeepSeek 查询翻译）
- [x] **混合检索**：BM25（jieba 分词）关键词检索 + 向量语义检索，RRF 按排名融合
- [x] JWT 用户认证（`auth.py` 哈希/签发/验证 + `/register` `/login` `/me`）
- [x] SQLite 持久化（用户表 + 对话历史 messages 表，参数化查询防注入）
- [x] 请求日志 + 耗时中间件、CORS 跨域
- [x] **引用溯源**（8/7）：回答附带完整来源——源文件名 + 命中原文片段（父块 excerpt），`/chat` 返回结构化 sources，前端引用卡片展示
- [ ] Rerank 重排序（bge-reranker，检索质量下一轮优化）
- [ ] Docker 部署 + 线上 URL（Week 6-7）

## RAG 评估现状（v2，2026-08-05）

- 9 题评估（宁德财报 2025/2026H1 + 货币政策报告）
- **内容级命中：22.2% → 66.7%**（混合检索后），文件级 8/9 → 9/9
- 评估脚本：`run_evaluation.py`（`USE_HYBRID` 开关对比）；记录见 `4.RAG/评估记录.md`
- 遗留短板：财报数字类（营收/净利）检索不到，下轮方向 Rerank / 表格结构感知分块

## 本地运行

```bash
# 1. 后端：用户认证 + 问答 API（终端 1，进入 rag_system 目录）
cd 4.RAG/rag_system
.\.venv\Scripts\python.exe -m uvicorn auth_api_db:app --port 8000

# 2. RAG 命令行交互入口（终端 2，可选）
cd 4.RAG/rag_system
.\.venv\Scripts\python.exe main.py

# 3. RAG 评估（终端 2）
cd 4.RAG
rag_system\.venv\Scripts\python.exe run_evaluation.py
```

## 目录结构

```
rag_system/
├── src/                    # RAG 核心模块
│   ├── document_loader.py  # 文档加载（PDF）
│   ├── text_processor.py   # 文本清洗 + 父子分块（200/1500）
│   ├── vector_store.py     # 向量存储（ChromaDB + get_all_chunks）
│   ├── retriever.py        # 混合检索（BM25+向量+RRF）+ LLM 生成
│   └── rag_pipeline.py     # 完整 RAG 流水线装配
├── api.py                  # RAG 问答 API 外壳
├── main.py                 # RAG 命令行交互入口
├── auth.py                 # JWT + 密码哈希工具
├── auth_api_db.py          # 用户系统 API（SQLite 持久化版，当前使用）
├── db.py                   # SQLite 初始化 + 用户/对话表操作
├── requirements.txt        # 依赖清单
├── .gitignore              # 忽略 .env/.venv/chroma_db/users.db 等
├── .env.example            # 环境变量模板（复制为 .env 填入 Key）
└── 项目结构.md             # 结构说明
```

## 环境变量（.env）

```
OPENAI_API_KEY=你的DeepSeek_API_Key
```

> 真实 `.env` 不入 Git；使用前复制 `.env.example` 为 `.env` 并填入 Key。

## 作者

- 广州理工学院 · 人工智能专业
- 学习路线：AI 应用开发工程师（Python + SQL + RAG + Agent）
