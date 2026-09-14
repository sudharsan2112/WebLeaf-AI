from typing import List, Dict, Any
from .config import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter

class Chunker:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = document.get("text", "")
        if not text:
            return []

        chunks = self.text_splitter.split_text(text)
        
        chunk_docs = []
        for chunk in chunks:
            chunk_docs.append({
                "url": document.get("url"),
                "title": document.get("title"),
                "text": chunk
            })
            
        return chunk_docs
