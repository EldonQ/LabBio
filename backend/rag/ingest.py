"""
RAG Ingestion with Structured Markdown Support
==============================================
Ingests structured protocols (.md) with YAML frontmatter.
"""

import os
import re
import yaml
from typing import List, Dict, Any
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import sys

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config import load_config

# Initialize Configuration
config = load_config()
PERSIST_DIRECTORY = config['rag']['persist_directory']
COLLECTION_NAME = config['rag']['collection_name']
EMBEDDING_MODEL = config['rag']['embedding_model']

def parse_markdown_protocol(file_path: Path) -> List[Document]:
    """
    Parses a structured Markdown protocol with YAML frontmatter.
    Splits by H1 headers (#).
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 1. Extract Frontmatter
    frontmatter = {}
    markdown_content = content
    
    if content.startswith("---"):
        try:
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                markdown_content = parts[2]
        except Exception as e:
            print(f"⚠️ Error parsing frontmatter for {file_path.name}: {e}")
            
    protocol_name = frontmatter.get("protocol_name", file_path.stem)
    description = frontmatter.get("description", "")
    tags = frontmatter.get("tags", [])
    
    # 2. Split by Headers (# )
    # We want to keep the header in the chunk
    chunks = []
    
    # Add a "Summary" chunk based on frontmatter
    summary_text = f"Protocol: {protocol_name}\nDescription: {description}\nTags: {', '.join(tags)}"
    chunks.append(Document(
        page_content=summary_text,
        metadata={
            "source": file_path.name,
            "type": "protocol_summary",
            "protocol": protocol_name,
            "tags": str(tags)
        }
    ))
    
    # Regex to split by # Header
    # This is a simple splitter; for more complex md, consider RecursiveCharacterTextSplitter
    sections = re.split(r'(^#\s+.*$)', markdown_content, flags=re.MULTILINE)
    
    current_header = "Introduction"
    current_text = []
    
    for section in sections:
        if section.strip().startswith('#'):
            # Save previous section
            if current_text:
                text = "\n".join(current_text).strip()
                if text:
                    chunks.append(Document(
                        page_content=f"{current_header}\n{text}", # Include header in content for context
                        metadata={
                            "source": file_path.name,
                            "type": "protocol_section",
                            "protocol": protocol_name,
                            "section": current_header,
                            "tags": str(tags)
                        }
                    ))
            # Start new section
            current_header = section.strip().lstrip('#').strip()
            current_text = []
        else:
            current_text.append(section)
            
    # Add last section
    if current_text:
        text = "\n".join(current_text).strip()
        if text:
            chunks.append(Document(
                page_content=f"{current_header}\n{text}",
                metadata={
                    "source": file_path.name,
                    "type": "protocol_section",
                    "protocol": protocol_name,
                    "section": current_header,
                    "tags": str(tags)
                }
            ))
            
    return chunks

def load_documents(docs_dir: Path) -> List[Document]:
    """Load all documents"""
    documents = []
    
    # Load new Structured Protocols
    protocol_dir = docs_dir / "protocols"
    if protocol_dir.exists():
        for file_path in protocol_dir.glob("*.md"):
            print(f"📄 Processing Structured Protocol: {file_path.name}")
            docs = parse_markdown_protocol(file_path)
            documents.extend(docs)
            
    # Load Legacy Text Protocols (Optional: Keep them for now or deprecate)
    # For now, let's keep them but maybe prioritize the new ones
    for file_path in docs_dir.glob("*.txt"):
        print(f"📄 Processing Legacy Protocol: {file_path.name}")
        # Reuse old logic (simplified here)
        with open(file_path, 'r', encoding='utf-8') as f:
            documents.append(Document(
                page_content=f.read(),
                metadata={"source": file_path.name, "type": "legacy"}
            ))
            
    return documents

def ingest_knowledge_base():
    """Main ingestion function"""
    docs_dir = Path(__file__).parent.parent.parent / "Documents" / "Lab"
    
    print(f"📂 Loading documents from {docs_dir}...")
    documents = load_documents(docs_dir)
    print(f"🔪 Split into {len(documents)} chunks.")
    
    print(f"🧠 Initializing Embedding Model ({EMBEDDING_MODEL})...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'}
    )
    
    print(f"📦 Creating ChromaDB in {PERSIST_DIRECTORY}...")
    # Note: This will append to existing DB. To rebuild, delete the folder first.
    # For this upgrade, we should probably clear the DB to avoid duplicates/legacy mess.
    import shutil
    if os.path.exists(PERSIST_DIRECTORY):
        print("🧹 Clearing old Knowledge Base...")
        shutil.rmtree(PERSIST_DIRECTORY)
        
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY,
        collection_name=COLLECTION_NAME
    )
    
    print("✅ Knowledge Base Rebuilt Successfully!")
    
    # Test Retrieval
    print("\n🔎 Testing Retrieval (Query: 'QIIME2 import manifest format')...")
    results = vectorstore.similarity_search("QIIME2 import manifest format", k=1)
    for doc in results:
        print(f"--- Source: {doc.metadata['source']} ---")
        print(doc.page_content[:200] + "...")

if __name__ == "__main__":
    ingest_knowledge_base()
