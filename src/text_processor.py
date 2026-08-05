"""文本处理模块（v2：父子文档检索）"""
import re
import hashlib
from typing import List, Dict

class TextProcessor:
    """
    文本处理器（父子文档检索版）
    
    子块（child_size=200）：用于 Embedding 和向量检索，语义集中
    父块（parent_size=1500）：检索命中后喂给 LLM，上下文完整
    每个子块在 metadata 中存储其所属父块的完整文本
    """
    
    def __init__(self, child_size: int = 200, parent_size: int = 1500, overlap: int = 50):
        self.child_size = child_size
        self.parent_size = parent_size
        self.overlap = overlap
    
    def process(self, document: Dict) -> List[Dict]:
        text = self._clean_text(document['text'])
        parent_chunks = self._chunk_text(text, self.parent_size)
        processed_chunks = []
        global_index = 0
        
        for parent_idx, parent_text in enumerate(parent_chunks):
            child_chunks = self._chunk_text(parent_text, self.child_size)
            for child_idx, child_text in enumerate(child_chunks):
                chunk_id = self._generate_chunk_id(
                    document['metadata']['source'], global_index
                )
                processed_chunks.append({
                    'text': child_text,
                    'metadata': {
                        **document['metadata'],
                        'chunk_id': chunk_id,
                        'chunk_index': global_index,
                        'total_chunks': 0,
                        'chunk_size': len(child_text),
                        'parent_index': parent_idx,
                        'child_index': child_idx,
                        'parent_text': parent_text,
                        'parent_size': len(parent_text),
                        'child_size': len(child_text),
                        'strategy': 'parent_document'
                    }
                })
                global_index += 1
        
        total = len(processed_chunks)
        for chunk in processed_chunks:
            chunk['metadata']['total_chunks'] = total
        
        return processed_chunks
    
    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = text.strip()
        text = text.encode('utf-8', errors='replace').decode('utf-8')
        return text
    
    def _chunk_text(self, text: str, target_size: int) -> List[str]:
        chunks = []
        start = 0
        step = target_size - self.overlap
        while start < len(text):
            end = start + target_size
            chunk = text[start:end]
            if end < len(text):
                last_period = chunk.rfind('。')
                if last_period > target_size * 0.5:
                    chunk = chunk[:last_period + 1]
            chunks.append(chunk)
            start += step
        return chunks
    
    @staticmethod
    def _generate_chunk_id(file_path: str, chunk_index: int) -> str:
        file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        return f'{file_hash}_chunk_{chunk_index}'