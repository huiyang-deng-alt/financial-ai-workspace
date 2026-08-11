"""检索模块（v2：父文档检索）"""
from typing import List, Dict
from openai import OpenAI
import jieba
from rank_bm25 import BM25Okapi

# Rerank 精排的候选池大小：先召回 50 条，再精排取 top_k
RERANK_CANDIDATES = 50

class Retriever:
    """检索器（父子文档检索版）"""

    def hybrid_search(self, query: str, top_k: int = 3, use_rerank: bool = False) -> Dict:
        """混合检索：向量（语义）+ BM25（关键词）→ RRF 融合；use_rerank=True 时先召回 50 条再精排"""
        recall_k = RERANK_CANDIDATES if use_rerank else top_k
        # 1. 向量路：中文先翻译成英文（适配英文 Embedding）
        vec = self.vector_store.search(self._translate_query(query), top_k=recall_k)
        vec_entries = [
            {"chunk_id": m.get("chunk_id", f"vec_{i}"), "text": t, "metadata": m}
            for i, (t, m) in enumerate(zip(vec["documents"], vec["metadatas"]))
        ]

        # 2. BM25 路：原始中文直接分词检索（不翻译，绕开失真）
        bm25_entries = [
            {"chunk_id": self.bm25_metas[i].get("chunk_id", f"bm25_{i}"),
             "text": self.bm25_docs[i], "metadata": self.bm25_metas[i]}
            for i in self._bm25_search(query, top_k=recall_k)
        ]

        # 3. RRF 融合，输出格式和 vector_store.search 保持一致
        fused = self._rrf_merge([vec_entries, bm25_entries], recall_k)

        # 4.（可选）Rerank 精排：交叉编码器逐条打分，取最终 top_k
        if use_rerank and fused:
            fused = self._rerank_entries(query, fused, top_k)
        return {
            "documents": [e["text"] for e in fused],
            "metadatas": [e["metadata"] for e in fused],
            "distances": [0.0] * len(fused),
        }
    
    def __init__(self, vector_store, llm_client: OpenAI):
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.reranker = None  # Rerank 模型懒加载（首次精排时才加载）
        chunks = vector_store.get_all_chunks()
        self.bm25_docs = [chunk["text"] for chunk in chunks]
        self.bm25_metas = [chunk["metadata"] for chunk in chunks]
        self.bm25_index = BM25Okapi([list(jieba.cut(t)) for t in self.bm25_docs])
    
    def retrieve_and_generate(
        self, 
        query: str, 
        top_k: int = 3,
        model: str = "deepseek-chat",
        use_rerank: bool = True
    ) -> Dict:
        search_results = self.hybrid_search(query, top_k=top_k, use_rerank=use_rerank)
        
        if not search_results['documents']:
            return {
                'answer': "抱歉，我没有找到相关信息。",
                'sources': [],
                'retrieved_docs': []
            }
        
        # 2. 从子块 metadata 中提取父块文本（去重）
        parent_texts = self._extract_parent_texts(
            search_results['metadatas'],
            search_results['documents']
        )
        
        # 3. 用父块构造上下文
        context = self._build_context(parent_texts)
        prompt = self._build_prompt(query, context)
        
        # 4. 调用 LLM 生成答案
        response = self.llm_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个有帮助的助手，请基于提供的文档回答问题。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        answer = response.choices[0].message.content
        
        # 5. 整理来源
        sources = self._extract_sources(search_results['metadatas'])
        
        return {
            'answer': answer,
            'sources': sources,
            'retrieved_docs': parent_texts
        }
    
    def retrieve_and_generate_stream(
        self,
        query: str,
        top_k: int = 3,
        model: str = "deepseek-chat"
    ):
        search_results = self.vector_store.search(query, top_k=top_k)
        
        if not search_results['documents']:
            yield "抱歉，我没有找到相关信息。"
            return
        
        parent_texts = self._extract_parent_texts(
            search_results['metadatas'],
            search_results['documents']
        )
        
        context = self._build_context(parent_texts)
        prompt = self._build_prompt(query, context)
        
        stream = self.llm_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个有帮助的助手，请基于提供的文档回答问题。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    
    def _translate_query(self, query: str) -> str:
        """将中文查询翻译为英文（适配纯英文 Embedding 模型）"""
        # 如果已经是英文，直接返回
        if all(ord(c) < 128 for c in query.replace(' ', '')):
            return query
        
        response = self.llm_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "system",
                "content": "Translate the following Chinese question into English. Output ONLY the English translation, nothing else."
            }, {
                "role": "user",
                "content": query
            }],
            temperature=0.0,
            max_tokens=200
        )
        translated = response.choices[0].message.content.strip()
        print(f"[翻译] {query} -> {translated}")
        return translated

    def _bm25_search(self, query: str, top_k: int = 3) -> List[int]:
        """BM25 关键词检索：返回命中的子块索引（按分数降序）"""
        tokens = list(jieba.cut(query))
        scores = self.bm25_index.get_scores(tokens)
        return sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    @staticmethod
    def _rrf_merge(entries_list, top_k: int, k: int = 60) -> List[Dict]:
        """RRF 融合：每路结果只按'排名'加分，不看具体分数"""
        scores = {}
        meta_map = {}
        for entries in entries_list:
            for rank, entry in enumerate(entries):
                cid = entry["chunk_id"]
                scores[cid] = scores.get(cid, 0) + 1 / (k + rank + 1)
                meta_map[cid] = entry
        ranked = sorted(scores, key=scores.get, reverse=True)[:top_k]
        return [meta_map[cid] for cid in ranked]

    def _rerank_entries(self, query: str, candidates: List[Dict], top_k: int) -> List[Dict]:
        """用交叉编码器（bge-reranker）对候选精排；模型懒加载，GPU 优先"""
        if self.reranker is None:
            from src.reranker import Reranker
            self.reranker = Reranker()
        return self.reranker.rerank(query, candidates, top_k)

    @staticmethod
    def _extract_parent_texts(metadatas: List[Dict], child_texts: List[str]) -> List[str]:
        seen = set()
        parents = []
        for meta in metadatas:
            parent_text = meta.get('parent_text', '')
            if parent_text and parent_text not in seen:
                parents.append(parent_text)
                seen.add(parent_text)
        if not parents:
            for text in child_texts:
                if text not in seen:
                    parents.append(text)
                    seen.add(text)
        return parents
    
    @staticmethod
    def _build_context(documents: List[str]) -> str:
        context = ""
        for i, doc in enumerate(documents, 1):
            context += f"\n文档 {i}:\n{doc}\n"
        return context
    
    @staticmethod
    def _build_prompt(query: str, context: str) -> str:
        return f"""请根据以下文档回答问题。

文档内容：
{context}

问题：{query}

要求：
1. 只基于文档内容回答，不要编造信息
2. 如果文档中没有相关信息，请明确说明
3. 回答要准确、简洁
4. 如果可能，请引用文档中的原文

回答："""
    
    @staticmethod
    def _extract_sources(metadatas: List[Dict], max_excerpt: int = 200) -> List[Dict]:
        """提取来源：源文件名 + 命中原文片段（父块文本，按文件去重）"""
        sources = []
        seen = set()
        for meta in metadatas:
            source = meta.get('source', 'unknown')
            if source not in seen:
                excerpt = meta.get('parent_text', '') or ''
                if len(excerpt) > max_excerpt:
                    excerpt = excerpt[:max_excerpt] + '……'
                sources.append({
                    'source': source,
                    'filename': meta.get('filename', 'unknown'),
                    'excerpt': excerpt
                })
                seen.add(source)
        return sources
