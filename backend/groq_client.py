import httpx
import json
from typing import AsyncGenerator
from .config import settings
from .utils import get_logger

logger = get_logger(__name__)

class GroqClient:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.LLM_MODEL
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        if not self.api_key:
            yield "Error: GROQ_API_KEY is not set in environment variables."
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "temperature": settings.TEMPERATURE,
            "max_tokens": settings.MAX_TOKENS
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
        except Exception as e:
            logger.error(f"Error communicating with Groq API: {type(e).__name__} - {str(e)}")
            yield f"\n[Error communicating with Groq API: {type(e).__name__} - {str(e)}]"
