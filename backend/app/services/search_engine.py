"""
Semantic Bug Search Engine
FAISS-backed nearest-neighbour search over embedded GitHub issues.

Index lifecycle
---------------
  build_index(issues)  — encode all issues, create a flat L2 FAISS index, persist to disk
  load_index()         — deserialise index + metadata from disk
  search(query, k)     — embed query text, run ANN search, return annotated results

The index is stored under  data/processed/search_index/  relative to the project root.
"""

import json
import logging
import pickle
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.services.embedding_service import (
    EMBEDDING_DIM,
    build_bug_document,
    embed_batch,
    embed_text,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INDEX_DIR = _PROJECT_ROOT / "data" / "processed" / "search_index"
INDEX_FILE = INDEX_DIR / "bugs.index"
METADATA_FILE = INDEX_DIR / "metadata.pkl"
STATS_FILE = INDEX_DIR / "stats.json"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def build_index(issues: List[Dict[str, Any]], show_progress: bool = True) -> Dict[str, Any]:
    """
    Encode every issue and write a FAISS flat-L2 index to disk.

    Inner-product search on L2-normalised vectors == cosine similarity,
    so we use IndexFlatIP (faster shortlist retrieval for free).

    Args:
        issues:        List of raw GitHub issue dicts.
        show_progress: Show a tqdm bar during encoding.

    Returns:
        Stats dict.
    """
    try:
        import faiss
    except ImportError:
        raise RuntimeError("faiss-cpu is not installed. Run: pip install faiss-cpu")

    logger.info("Building search index for %d issues…", len(issues))
    t0 = time.perf_counter()

    # Build document strings
    documents = [build_bug_document(issue) for issue in issues]

    # Encode in batches
    vectors = embed_batch(documents, show_progress=show_progress)  # (N, 384)

    # FAISS index — Inner Product on L2-normalised vectors == cosine similarity
    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    index.add(vectors)

    # Persist
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_FILE))

    # Save lightweight metadata (no need to store full bodies in FAISS)
    metadata = []
    for i, issue in enumerate(issues):
        metadata.append({
            "index_id": i,
            "issue_id": issue.get("id", i),
            "number": issue.get("number"),
            "title": issue.get("title", ""),
            "url": issue.get("url", ""),
            "repository": issue.get("repository", ""),
            "state": issue.get("state", ""),
            "labels": issue.get("labels", []),
            "body_snippet": (issue.get("body") or "")[:400],
        })

    with open(METADATA_FILE, "wb") as f:
        pickle.dump(metadata, f, protocol=pickle.HIGHEST_PROTOCOL)

    elapsed = time.perf_counter() - t0
    stats = {
        "total_indexed": len(issues),
        "embedding_dim": EMBEDDING_DIM,
        "index_type": "IndexFlatIP (cosine)",
        "build_time_seconds": round(elapsed, 2),
        "index_size_kb": round(INDEX_FILE.stat().st_size / 1024, 1),
    }

    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

    logger.info("Index built in %.1fs — %d vectors stored", elapsed, len(issues))
    return stats


def is_index_available() -> bool:
    """Return True if an index file and its metadata file exist on disk."""
    return INDEX_FILE.exists() and METADATA_FILE.exists()


def load_index() -> Tuple[Any, List[Dict]]:
    """
    Load the FAISS index and metadata from disk.

    Returns:
        (faiss_index, metadata_list)

    Raises:
        FileNotFoundError: if the index has not been built yet.
    """
    try:
        import faiss
    except ImportError:
        raise RuntimeError("faiss-cpu is not installed. Run: pip install faiss-cpu")

    if not is_index_available():
        raise FileNotFoundError(
            "Search index not found. "
            "Run scripts/build_search_index.py first."
        )

    index = faiss.read_index(str(INDEX_FILE))
    with open(METADATA_FILE, "rb") as f:
        metadata = pickle.load(f)

    return index, metadata


# ---------------------------------------------------------------------------
# Module-level cache so the index is read from disk only once per process
# ---------------------------------------------------------------------------
_cached_index = None
_cached_metadata: Optional[List[Dict]] = None


def _get_index():
    global _cached_index, _cached_metadata
    if _cached_index is None:
        _cached_index, _cached_metadata = load_index()
    return _cached_index, _cached_metadata


def search_similar_bugs(
    query: str,
    k: int = 5,
    min_score: float = 0.25,
) -> List[Dict[str, Any]]:
    """
    Find the k most semantically similar bugs to a query string.

    Args:
        query:     Free-form error text, stack trace, or description.
        k:         Maximum number of results to return.
        min_score: Minimum cosine similarity (0–1) to include in results.

    Returns:
        List of result dicts sorted by descending similarity.
    """
    index, metadata = _get_index()

    query_vec = embed_text(query).reshape(1, -1)  # (1, 384)

    # Over-fetch, then filter by min_score
    fetch_k = min(k * 3, index.ntotal)
    scores, indices = index.search(query_vec, fetch_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        similarity = float(score)  # already in [0,1] for normalised IP
        if similarity < min_score:
            continue
        meta = metadata[idx].copy()
        meta["similarity_score"] = round(similarity, 4)
        meta["similarity_pct"] = f"{similarity * 100:.1f}%"
        results.append(meta)

    # Return top-k after filtering
    return results[:k]


def get_index_stats() -> Dict[str, Any]:
    """Return stats about the current index, or a 'not built' sentinel."""
    if not is_index_available():
        return {"status": "not_built", "message": "Run build_search_index.py to create the index"}

    if STATS_FILE.exists():
        with open(STATS_FILE) as f:
            stats = json.load(f)
        stats["status"] = "ready"
        return stats

    # Fallback: derive stats from FAISS object
    try:
        index, metadata = _get_index()
        return {
            "status": "ready",
            "total_indexed": index.ntotal,
            "embedding_dim": EMBEDDING_DIM,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
