from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Any

class CrawlRequest(BaseModel):
    url: HttpUrl

class CrawlResponse(BaseModel):
    message: str
    kb_id: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    kb_id: str
    session_id: str = "default"

class SourceReference(BaseModel):
    url: str
    title: str
    similarity_score: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceReference]

class StatusResponse(BaseModel):
    kb_id: str
    status: str
    pages_crawled: int
    chunks_created: int
    error: Optional[str] = None

class SettingsModel(BaseModel):
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    top_k: Optional[int] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
