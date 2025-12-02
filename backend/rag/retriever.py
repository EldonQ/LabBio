"""
RAG Retriever Module
====================
提供检索接口，用于Agent查询知识库。
"""

import yaml
from pathlib import Path
from typing import List

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

class LabKnowledgeRetriever:
    """实验室知识库检索器"""
    
    def __init__(self):
        """初始化检索器"""
        self.config = self._load_config()
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.vectorstore = self._load_vectorstore()
    
    def _load_config(self) -> dict:
        """加载配置"""
        from backend.config import load_config
        return load_config()
    
    def _load_vectorstore(self):
        """加载向量库"""
        persist_dir = self.config['rag']['persist_directory']
        collection_name = self.config['rag']['collection_name']
        
        vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings,
            collection_name=collection_name
        )
        return vectorstore
    
    def retrieve(self, query: str, k: int = 3) -> List[str]:
        """
        检索相关文档片段
        
        Args:
            query: 查询文本
            k: 返回的结果数量
            
        Returns:
            相关文档内容列表
        """
        results = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in results]
    
    def retrieve_with_sources(self, query: str, k: int = 3) -> List[dict]:
        """
        检索相关文档片段（带来源信息）
        
        Args:
            query: 查询文本
            k: 返回的结果数量
            
        Returns:
            包含content和source的字典列表
        """
        results = self.vectorstore.similarity_search(query, k=k)
        return [
            {
                'content': doc.page_content,
                'source': doc.metadata.get('source', 'unknown'),
                'type': doc.metadata.get('type', 'unknown')
            }
            for doc in results
        ]

# 全局单例
_retriever = None

def get_retriever() -> LabKnowledgeRetriever:
    """获取检索器单例"""
    global _retriever
    if _retriever is None:
        _retriever = LabKnowledgeRetriever()
    return _retriever

if __name__ == "__main__":
    # 测试检索器
    print("Testing Retriever...")
    retriever = get_retriever()
    
    query = "如何激活obitools"
    results = retriever.retrieve_with_sources(query, k=2)
    
    print(f"\nQuery: {query}")
    print(f"Found {len(results)} results:\n")
    
    for i, result in enumerate(results):
        print(f"[{i+1}] Source: {result['source']}")
        print(f"    Content: {result['content'][:150]}...")
        print()
