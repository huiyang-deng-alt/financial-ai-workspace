# ============ 前端镜像：Streamlit ============
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --timeout=300 --retries=5

COPY src ./src

# 深色主题配置一起进镜像
COPY .streamlit ./.streamlit

EXPOSE 8501

CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
