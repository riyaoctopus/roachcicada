"""In-memory embedding retrieval over the RoachCicada knowledge base.
Small corpus (a few hundred chunks) — plain numpy cosine similarity is
plenty fast and needs no vector DB for a local demo."""
import numpy as np

from common import load_chunks


class Retriever:
    def __init__(self):
        chunks = load_chunks()
        self.chunks = chunks
        vectors = np.array([c["embedding"] for c in chunks], dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        self.normed = vectors / norms

    def search(self, query_embedding, top_k: int = 6):
        q = np.array(query_embedding, dtype=np.float32)
        q = q / (np.linalg.norm(q) + 1e-9)
        scores = self.normed @ q
        top_idx = np.argsort(-scores)[:top_k]
        return [
            {**self.chunks[i], "score": float(scores[i])}
            for i in top_idx
        ]
