import logging
import numpy as np
from typing import List, Dict, Any, Optional

logger = logging.getLogger('mom_backend.search')

class VectorSearchService:
    def __init__(self):
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self._embedder = None
        # Memory storage: list of { "embedding": np.ndarray, "metadata": dict }
        self.documents = []

    def _get_embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.info(f"sentence_transformers not loaded: {e}. Using deterministic hashing vector space fallback.")
                self._embedder = None
        return self._embedder

    def compute_embedding(self, text: str) -> np.ndarray:
        embedder = self._get_embedder()
        if embedder:
            try:
                return embedder.encode(text, convert_to_numpy=True)
            except Exception:
                pass
                
        # Deterministic 64-dim normalized pseudo-embedding based on character n-grams
        vec = np.zeros(64, dtype=np.float32)
        for i, char in enumerate(text.lower()):
            vec[(ord(char) + i) % 64] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def index_meeting(self, user_id: int, meeting_id: int, title: str, summary: str, action_items: List[str], decisions: List[str]):
        """Indexes meeting components for isolated user vector search"""
        # Remove previous entries for this meeting
        self.documents = [d for d in self.documents if d["metadata"]["meeting_id"] != meeting_id]

        docs_to_add = [
            {"text": f"Meeting Title: {title}. {summary}", "type": "summary"},
        ]
        for a in action_items:
            docs_to_add.append({"text": f"Action Item: {a}", "type": "action"})
        for dec in decisions:
            docs_to_add.append({"text": f"Decision: {dec}", "type": "decision"})

        for item in docs_to_add:
            emb = self.compute_embedding(item["text"])
            self.documents.append({
                "embedding": emb,
                "metadata": {
                    "user_id": user_id,
                    "meeting_id": meeting_id,
                    "title": title,
                    "text": item["text"],
                    "type": item["type"]
                }
            })

    def search_user_meetings(self, user_id: int, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Searches documents strictly matching the authenticated user_id.
        Computes cosine similarity against query embedding.
        """
        user_docs = [d for d in self.documents if d["metadata"]["user_id"] == user_id]
        if not user_docs:
            return []

        query_emb = self.compute_embedding(query)
        results = []

        for doc in user_docs:
            emb = doc["embedding"]
            # Cosine similarity
            dot = float(np.dot(query_emb, emb))
            norm_q = float(np.linalg.norm(query_emb))
            norm_e = float(np.linalg.norm(emb))
            sim = dot / (norm_q * norm_e) if (norm_q * norm_e) > 0 else 0.0
            
            results.append({
                "meeting_id": doc["metadata"]["meeting_id"],
                "title": doc["metadata"]["title"],
                "text": doc["metadata"]["text"],
                "type": doc["metadata"]["type"],
                "similarity": round(sim, 4)
            })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

vector_search_service = VectorSearchService()
