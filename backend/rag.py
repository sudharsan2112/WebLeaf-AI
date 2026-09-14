import json
from typing import List, Dict, Any, AsyncGenerator, Tuple
from .embedder import Embedder
from .vector_store import VectorStore
from .groq_client import GroqClient
from .chat_memory import ChatMemory
from .config import settings
from .models import SourceReference
from .utils import get_logger

logger = get_logger(__name__)

class RAGPipeline:
    def __init__(self, kb_id: str, session_id: str = "default"):
        self.kb_id = kb_id
        self.embedder = Embedder()
        self.vector_store = VectorStore(kb_id)
        self.llm_client = GroqClient()
        self.memory = ChatMemory(session_id)

    async def get_context(self, query: str) -> List[Tuple[Dict[str, Any], float]]:
        query_embedding = await self.embedder.embed_query(query)
        if not query_embedding:
            return []
        results = self.vector_store.search(query_embedding, settings.TOP_K_RETRIEVAL)
        return results

    def build_prompt(self, query: str, context_docs: List[Tuple[Dict[str, Any], float]], history: List[Dict[str, str]]) -> str:
        prompt = "You are a helpful AI assistant answering questions based solely on the provided website context.\n\n"
        prompt += "CONTEXT:\n"
        
        for doc, score in context_docs:
            prompt += f"---\nSource URL: {doc.get('url')}\nTitle: {doc.get('title')}\nContent: {doc.get('text')}\n"
            
        prompt += "\nCHAT HISTORY:\n"
        for msg in history:
            prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
            
        prompt += f"\nUSER QUERY: {query}\n\n"
        prompt += (
            "INSTRUCTIONS:\n"
            "1. Only answer based on the CONTEXT provided above.\n"
            "2. Never hallucinate or invent information.\n"
            "3. If the answer is unavailable in the CONTEXT, respond exactly with: 'I could not find this information in the website.'\n"
            "4. Provide detailed, well-formatted answers in Markdown.\n\n"
            "ASSISTANT:"
        )
        return prompt

    async def chat_stream(self, query: str) -> AsyncGenerator[str, None]:
        try:
            context_docs = await self.get_context(query)
            self.memory.add_message("user", query)
        except Exception as e:
            logger.error(f"Chat setup failed: {type(e).__name__} - {str(e)}")
            yield json.dumps({
                "type": "error",
                "data": f"Failed to retrieve context or embeddings: {str(e)}"
            }) + "\n"
            return
        
        sources = [
            SourceReference(url=doc["url"], title=doc["title"], similarity_score=score).model_dump()
            for doc, score in context_docs
        ]
        
        yield json.dumps({"type": "sources", "data": sources}) + "\n"
        
        history = self.memory.get_history()
        prompt = self.build_prompt(query, context_docs, history)
        
        full_response = ""
        async for chunk in self.llm_client.generate_stream(prompt):
            full_response += chunk
            yield json.dumps({"type": "chunk", "data": chunk}) + "\n"
            
        self.memory.add_message("assistant", full_response)
