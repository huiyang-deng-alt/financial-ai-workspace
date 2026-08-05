"""文档加载模块"""
import os
from typing import List, Dict
import PyPDF2
from docx import Document
from bs4 import BeautifulSoup

class DocumentLoader:
    """文档加载器"""
    
    @staticmethod
    def load_file(file_path: str) -> Dict:
        """
        加载单个文件
        
        Returns:
            Dict: {'text': str, 'metadata': dict}
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.txt' or ext == '.md':
            text = DocumentLoader._load_text(file_path)
        elif ext == '.pdf':
            text = DocumentLoader._load_pdf(file_path)
        elif ext in ['.doc', '.docx']:
            text = DocumentLoader._load_word(file_path)
        elif ext in ['.html', '.htm']:
            text = DocumentLoader._load_html(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
        
        return {
            'text': text,
            'metadata': {
                'source': file_path,
                'filename': os.path.basename(file_path),
                'extension': ext
            }
        }
    
    @staticmethod
    def load_directory(dir_path: str) -> List[Dict]:
        """加载目录下的所有文档"""
        documents = []
        
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    doc = DocumentLoader.load_file(file_path)
                    documents.append(doc)
                    print(f"[OK] 加载: {file}")
                except Exception as e:
                    print(f"[SKIP] 跳过: {file} ({e})")
        
        return documents
    
    @staticmethod
    def _load_text(file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def _load_pdf(file_path: str) -> str:
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    @staticmethod
    def _load_word(file_path: str) -> str:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    
    @staticmethod
    def _load_html(file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text()
