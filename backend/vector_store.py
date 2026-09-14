import os
import faiss
import pickle
import numpy as np
from typing import List, Dict, Any, Tuple
from .config import settings
from .utils import get_logger

logger = get_logger(__name__)

class VectorStore:
    def __init__(self, kb_id: str):
        self.kb_id = kb_id
        self.index_path = os.path.join(settings.FAISS_INDEX_DIR, f"{kb_id}.index")
        self.metadata_path = os.path.join(settings.FAISS_INDEX_DIR, f"{kb_id}_meta.pkl")
        self.index = None
        self.metadata = []
        # Default embedding dimension for all-MiniLM-L6-v2 is 384
        self.dimension = 384  
        self._load()

    def _load(self):
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, "rb") as f:
                self.metadata = pickle.load(f)
            logger.info(f"Loaded existing vector store for {self.kb_id}")
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
            logger.info(f"Created new vector store for {self.kb_id}")

    def add_embeddings(self, embeddings: List[List[float]], metadata: List[Dict[str, Any]]):
        if not embeddings:
            return
        
        embeddings_np = np.array(embeddings).astype('float32')
        if self.index is None or self.index.d != embeddings_np.shape[1]:
            self.dimension = embeddings_np.shape[1]
            self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings_np)
        self.metadata.extend(metadata)
        
        # Save to disk
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if not self.index or self.index.ntotal == 0:
            return []

        query_np = np.array([query_embedding]).astype('float32')
        distances, indices = self.index.search(query_np, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                results.append((self.metadata[idx], float(distances[0][i])))
        return results

    def delete(self):
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        if os.path.exists(self.metadata_path):
            os.remove(self.metadata_path)
