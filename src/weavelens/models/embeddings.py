from __future__ import annotations
from sentence_transformers import SentenceTransformer
from ..settings import Settings

_model: SentenceTransformer | None = None

def get_embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        s = Settings()
        _model = SentenceTransformer(s.emb_model_name, cache_folder=s.models_cache, device=s.emb_device)
        _model.max_seq_length = s.emb_max_seq
    return _model

def embed_texts(texts: list[str]) -> list[list[float]]:
    m = get_embedder()
    embs = m.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [e.tolist() for e in embs]
