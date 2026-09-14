from typing import List
from sentence_transformers import SentenceTransformer
from .config import settings
from .utils import get_logger

logger = get_logger(__name__)

# Load model globally to avoid reloading on every request
try:
    _model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.error(f"Failed to load sentence-transformers model: {e}")
    _model = None

class Embedder:
    def __init__(self):
        self.model = _model
        if not self.model:
            raise RuntimeError("Embedding model not loaded successfully.")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            # sentence-transformers encodes synchronously, so we could use a threadpool, 
            # but for this scale direct encoding is fast enough.
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise

    async def embed_query(self, query: str) -> List[float]:
        embeddings = await self.generate_embeddings([query])
        if embeddings:
            return embeddings[0]
        return []
