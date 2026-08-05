"""主程序"""
import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

from src.rag_pipeline import RAGPipeline

def main():
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key")
    DATA_DIR = "./data"
    
    print("初始化 RAG Pipeline（父子文档检索模式）...")
    pipeline = RAGPipeline(
        openai_api_key=OPENAI_API_KEY,
        db_path="./chroma_db",
        collection_name="my_knowledge_base",
        child_size=200,
        overlap=50
    )
    
    if input("是否需要重新摄入文档？(y/n): ").lower() == 'y':
        pipeline.ingest_directory(DATA_DIR)
    
    stats = pipeline.get_stats()
    print(f"\n数据库统计: {stats['total_chunks']} 个子块")
    
    print("\n" + "=" * 50)
    print("RAG 系统已就绪！输入 'quit' 退出")
    print("=" * 50)
    
    while True:
        question = input("\n你的问题: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        if not question:
            continue
        
        print("\n思考中...")
        result = pipeline.query(question, top_k=3)
        
        print("\n" + "=" * 50)
        print("回答:")
        print(result['answer'])
        
        if result['sources']:
            print("\n来源:")
            for i, source in enumerate(result['sources'], 1):
                print(f"{i}. {source['filename']}")
        
        print("=" * 50)

if __name__ == "__main__":
    main()