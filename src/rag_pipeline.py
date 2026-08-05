"""RAG Pipeline 主模块"""
from typing import List
from openai import OpenAI
from .document_loader import DocumentLoader
from .text_processor import TextProcessor
from .vector_store import VectorStore
from .retriever import Retriever

class RAGPipeline:
    """完整的 RAG Pipeline（父子文档检索版）"""
    
    def __init__(
        self,
        openai_api_key: str,
        db_path: str = "./chroma_db",
        collection_name: str = "documents",
        child_size: int = 200,
        overlap: int = 50
    ):
        self.loader = DocumentLoader()
        self.processor = TextProcessor(child_size=child_size, parent_size=1500, overlap=overlap)
        self.vector_store = VectorStore(db_path=db_path, collection_name=collection_name)
        self.llm_client = OpenAI(api_key=openai_api_key, base_url="https://api.deepseek.com")
        self.retriever = Retriever(self.vector_store, self.llm_client)
    
    def ingest_directory(self, dir_path: str):
        print(f"\n开始处理目录: {dir_path}")
        print("=" * 50)
        
        print("\n[1/3] 加载文档...")
        documents = self.loader.load_directory(dir_path)
        print(f"[OK] 成功加载 {len(documents)} 个文档")
        
        print("\n[2/3] 处理文档（父子分块：子块200字检索 + 父块1500字喂LLM）...")
        all_chunks = []
        for doc in documents:
            chunks = self.processor.process(doc)
            all_chunks.extend(chunks)
        print(f"[OK] 生成 {len(all_chunks)} 个子块")
        
        print("\n[3/3] 存储到向量数据库...")
        self.vector_store.add_chunks(all_chunks)
        print(f"[OK] 完成！数据库中共有 {self.vector_store.count()} 个子块")
    
    def query(self, question: str, top_k: int = 3) -> dict:
        return self.retriever.retrieve_and_generate(question, top_k=top_k)
    
    def query_stream(self, question: str, top_k: int = 3):
        return self.retriever.retrieve_and_generate_stream(question, top_k=top_k)
    
    def get_stats(self) -> dict:
        return {'total_chunks': self.vector_store.count()}