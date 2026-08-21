"""Rerank 精排模块：交叉编码器 bge-reranker-base（GPU 优先，模型在 ./models/bge-reranker-base）"""
import os
from typing import List, Dict

MODEL_PATH = os.environ.get("RERANK_MODEL_PATH", "./models/bge-reranker-base")


class Reranker:
    """交叉编码器精排：对 RRF 融合后的候选逐条打分，返回 top_k。
    双塔（向量/BM25）负责召回，交叉编码器负责'哪条能回答这个问题'。"""

    def __init__(self, model_path: str = MODEL_PATH):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()
        self.model.to(self.device)
        print(f"[Reranker] 模型加载完成 device={self.device}")

    def rerank(self, query: str, candidates: List[Dict], top_k: int = 3) -> List[Dict]:
        """按'能否回答该问题'打分重排，返回 top_k 条（候选不足时原样截断）"""
        if not candidates:
            return candidates
        if top_k >= len(candidates):
            return candidates[:top_k]
        import torch
        pairs = [[query, c["text"]] for c in candidates]
        inputs = self.tokenizer(
            pairs, padding=True, truncation=True, max_length=512, return_tensors="pt"
        ).to(self.device)
        with torch.no_grad():
            scores = self.model(**inputs, return_dict=True).logits.view(-1,).float()
        ranked = sorted(zip(candidates, scores.tolist()), key=lambda x: x[1], reverse=True)
        return [c for c, _ in ranked[:top_k]]