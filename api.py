"""RAG System - FastAPI 外壳（不移动任何文件）"""
import os, sys
from pathlib import Path

# 确保在 rag_system 目录下
os.chdir(Path(__file__).resolve().parent)

# 指向已有的 HF 缓存
os.environ["HF_HOME"] = str(Path(".hf_cache").resolve())
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.rag_pipeline import RAGPipeline

app = FastAPI(title="RAG API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

pipeline = RAGPipeline(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    db_path="./chroma_db",
    collection_name="my_knowledge_base",
)

class ChatRequest(BaseModel):
    question: str

@app.get("/")
def root():
    return {"message": "RAG API", "chunks": pipeline.get_stats()["total_chunks"]}

@app.post("/chat")
def chat(req: ChatRequest):
    result = pipeline.query(req.question, top_k=3)
    return {"answer": result["answer"], "sources": result["sources"]}

