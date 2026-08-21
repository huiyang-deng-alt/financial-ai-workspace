# ============ 后端镜像：FastAPI + RAG ============

# 基础镜像：装了 Python 3.12 的轻量 Linux
FROM python:3.12-slim

# 容器内工作目录（后续命令都在这里跑）
WORKDIR /app

# 先把依赖清单拷进来（利用 Docker 缓存层）
COPY requirements.txt .

# 装依赖（镜像最大的一层）
RUN pip install --no-cache-dir -r requirements.txt --timeout=300 --retries=5

# 把后端代码拷进镜像
COPY . .

# 离线模型路径固定到容器内 .hf_cache（模型文件通过挂载卷提供）
ENV HF_HOME=/app/.hf_cache \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

# 声明容器对外端口（只是声明，真正映射在 compose 里）
EXPOSE 8000

CMD ["uvicorn", "rag_app:app", "--host", "0.0.0.0", "--port", "8000"]
