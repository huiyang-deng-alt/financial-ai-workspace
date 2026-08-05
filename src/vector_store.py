import os as _os
from pathlib import Path as _Path
# Redirect HuggingFace cache to writable location
_hf_cache = _Path(__file__).parent.parent / ".hf_cache"
_os.environ["HF_HOME"] = str(_hf_cache)
_os.environ["HUGGINGFACE_HUB_CACHE"] = str(_hf_cache / "hub")
_os.environ["HF_HUB_OFFLINE"] = "1"  # 模型已缓存，跳过联网检查

"""向量存储模块"""
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from typing import List, Dict


def _sanitize(text):
    """移除 surrogate 字符，ChromaDB Rust 底层不接受"""
    return text.encode("utf-8", errors="replace").decode("utf-8")

class VectorStore:
    """向量存储"""
    
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "documents"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_fn
        )
    
    def add_chunks(self, chunks: List[Dict], batch_size: int = 100):
        total = len(chunks)
        for i in range(0, total, batch_size):
            batch = chunks[i:i+batch_size]
            texts = [_sanitize(chunk["text"]) for chunk in batch]
            metadatas = [{k: _sanitize(str(v)) for k, v in chunk["metadata"].items()} for chunk in batch]
            ids = [chunk["metadata"]["chunk_id"] for chunk in batch]
            self.collection.add(documents=texts, metadatas=metadatas, ids=ids)
            print(f"已添加 {min(i+batch_size, total)}/{total} 个文本块")
    
    def search(self, query: str, top_k: int = 3, filter_dict: Dict = None) -> Dict:
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=filter_dict
        )
        return {
            "documents": results["documents"][0],
            "metadatas": results["metadatas"][0],
            "distances": results["distances"][0]
        }
    
    def count(self) -> int:
        return self.collection.count()
    
    def clear(self):
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_fn
        )

    def get_all_chunks(self):
        """读出库里所有子块（建 BM25 索引用）"""
        data = self.collection.get()
        return [
            {"text": text, "metadata": meta}
            for text, meta in zip(data["documents"], data["metadatas"])
        ]