import os
import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from fastapi.staticfiles import StaticFiles

from .models import CrawlRequest, CrawlResponse, ChatRequest, StatusResponse, SettingsModel
from .crawler import WebCrawler
from .database import get_kb, delete_kb_record
from .rag import RAGPipeline
from .config import settings
from .chat_memory import ChatMemory

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

@app.get("/health")
async def health():
    return {"status": "ok"}
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest):
    url_str = str(request.url)
    kb_id = WebCrawler.start_crawl_task(url_str)
    return CrawlResponse(message="Crawling started", kb_id=kb_id)

@app.post("/chat")
async def chat(request: ChatRequest):
    kb = get_kb(request.kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
        
    rag = RAGPipeline(request.kb_id, request.session_id)
    return StreamingResponse(rag.chat_stream(request.message), media_type="application/x-ndjson")

@app.get("/status", response_model=StatusResponse)
async def get_status(kb_id: str):
    kb = get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
        
    return StatusResponse(
        kb_id=kb["kb_id"],
        status=kb["status"],
        pages_crawled=kb["pages_crawled"],
        chunks_created=kb["chunks_created"],
        error=kb["error_message"]
    )

@app.get("/history")
async def get_history(session_id: str):
    memory = ChatMemory(session_id)
    return {"history": memory.get_history()}

@app.delete("/delete")
async def delete_kb(kb_id: str):
    kb = get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    delete_kb_record(kb_id)
    
    index_path = os.path.join(settings.FAISS_INDEX_DIR, f"{kb_id}.index")
    metadata_path = os.path.join(settings.FAISS_INDEX_DIR, f"{kb_id}_meta.pkl")
    
    if os.path.exists(index_path):
        os.remove(index_path)
    if os.path.exists(metadata_path):
        os.remove(metadata_path)
        
    return {"message": "Knowledge base deleted"}

@app.post("/refresh")
async def refresh_kb(kb_id: str):
    kb = get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
        
    base_url = kb["base_url"]
    new_kb_id = WebCrawler.start_crawl_task(base_url)
    return {"message": "Refresh started", "kb_id": new_kb_id}

@app.get("/settings", response_model=SettingsModel)
async def get_app_settings():
    return SettingsModel(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        top_k=settings.TOP_K_RETRIEVAL,
        temperature=settings.TEMPERATURE,
        max_tokens=settings.MAX_TOKENS,
        llm_model=settings.LLM_MODEL,
        embedding_model=settings.EMBEDDING_MODEL
    )

@app.post("/settings")
async def update_app_settings(new_settings: SettingsModel):
    if new_settings.chunk_size: settings.CHUNK_SIZE = new_settings.chunk_size
    if new_settings.chunk_overlap: settings.CHUNK_OVERLAP = new_settings.chunk_overlap
    if new_settings.top_k: settings.TOP_K_RETRIEVAL = new_settings.top_k
    if new_settings.temperature is not None: settings.TEMPERATURE = new_settings.temperature
    if new_settings.max_tokens: settings.MAX_TOKENS = new_settings.max_tokens
    if new_settings.llm_model: settings.LLM_MODEL = new_settings.llm_model
    if new_settings.embedding_model: settings.EMBEDDING_MODEL = new_settings.embedding_model
    return {"message": "Settings updated"}

app.mount("/", StaticFiles(directory=os.path.join(settings.BASE_DIR, "frontend"), html=True), name="frontend")
