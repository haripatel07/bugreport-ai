"""
Embedding Service
Converts bug text into dense vector representations for semantic search.
Uses sentence-transformers (all-MiniLM-L6-v2) — lightweight, fast, no API key needed.
"""

import logging
import hashlib
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Lazy-loaded to avoid slowing down imports on the hot path
_model = None
_model_name = "all-MiniLM-L6-v2"

EMBEDDING_DIM = 384  # dimension for all-MiniLM-L6-v2


def _get_model():
    """Return the shared SentenceTransformer model, loading it on first call."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformer model: %s", _model_name)
            _model = SentenceTransformer(_model_name)
            logger.info("Model loaded successfully")
        except ImportError:
            raise RuntimeError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            )
    return _model


def embed_text(text: str) -> np.ndarray:
    """
    Embed a single piece of text.

    Args:
        text: Raw string to embed.

    Returns:
        Float32 numpy array of shape (EMBEDDING_DIM,).
    """
    if not text or not text.strip():
        return np.zeros(EMBEDDING_DIM, dtype=np.float32)

    model = _get_model()
    vector = model.encode(text.strip(), convert_to_numpy=True, normalize_embeddings=True)
    return vector.astype(np.float32)


def embed_batch(texts: List[str], batch_size: int = 64, show_progress: bool = False) -> np.ndarray:
    """
    Embed a list of texts efficiently using batched inference.

    Args:
        texts: List of raw strings.
        batch_size: Number of texts to encode per forward pass.
        show_progress: Show a tqdm progress bar (useful for large corpora builds).

    Returns:
        Float32 numpy array of shape (len(texts), EMBEDDING_DIM).
    """
    if not texts:
        return np.zeros((0, EMBEDDING_DIM), dtype=np.float32)

    # Replace empty strings with a placeholder so the model doesn't choke
    cleaned = [t.strip() if t and t.strip() else "<empty>" for t in texts]

    model = _get_model()
    vectors = model.encode(
        cleaned,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return vectors.astype(np.float32)


def build_bug_document(issue: dict) -> str:
    """
    Flatten a raw GitHub issue dict into a single searchable string.

    The title carries the most signal, so it is repeated for mild boosting.
    Large bodies are truncated to keep embeddings focused.

    Args:
        issue: Dict with keys like title, body, labels, repository.

    Returns:
        A plain-text document string ready for embedding.
    """
    parts: List[str] = []

    title = (issue.get("title") or "").strip()
    if title:
        parts.append(title)
        parts.append(title)  # slight weight boost

    body = (issue.get("body") or "").strip()
    if body:
        # Truncate very long bodies — embeddings degrade beyond ~512 tokens
        parts.append(body[:1200])

    labels = issue.get("labels") or []
    if isinstance(labels, list) and labels:
        label_str = " ".join(
            lbl.get("name", "") if isinstance(lbl, dict) else str(lbl)
            for lbl in labels
        )
        if label_str.strip():
            parts.append(label_str)

    repo = issue.get("repository", "")
    if repo:
        parts.append(repo)

    return " ".join(parts)


def compute_text_hash(text: str) -> str:
    """Return a short hash of the text, used to cache embeddings by content."""
    return hashlib.md5(text.encode("utf-8"), usedforsecurity=False).hexdigest()[:12]
