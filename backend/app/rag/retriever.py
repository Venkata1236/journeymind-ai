import json
import faiss
import numpy as np
from pathlib import Path
from loguru import logger
from openai import OpenAI
from app.core.config import get_settings

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)

INDEX_PATH = Path(settings.faiss_index_path)
METADATA_PATH = INDEX_PATH / "travel_metadata.json"
FAISS_FILE = INDEX_PATH / "travel.index"
EMBEDDING_MODEL = "text-embedding-ada-002"

# Module-level cache — loaded once, reused across all requests
_index = None
_metadata = None


def _load_index():
    """Load FAISS index and metadata into module-level cache."""
    global _index, _metadata

    if _index is not None and _metadata is not None:
        return  # Already loaded

    if not FAISS_FILE.exists():
        logger.error(f"FAISS index not found at {FAISS_FILE}. Run embedder.py first.")
        raise FileNotFoundError(f"FAISS index not found. Run: python -m app.rag.embedder")

    if not METADATA_PATH.exists():
        logger.error(f"Metadata not found at {METADATA_PATH}")
        raise FileNotFoundError(f"Metadata not found at {METADATA_PATH}")

    logger.info("Loading FAISS index into memory...")
    _index = faiss.read_index(str(FAISS_FILE))

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        _metadata = json.load(f)

    logger.success(f"FAISS index loaded — {_index.ntotal} vectors, {len(_metadata)} metadata entries")


def _embed_query(query: str) -> np.ndarray:
    """Embed a single query string."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query],
    )
    vector = np.array(response.data[0].embedding, dtype=np.float32)
    return vector.reshape(1, -1)


def search(query: str, top_k: int = 5, city_filter: str = None) -> list[dict]:
    """
    Search FAISS index for top_k most relevant travel reviews.

    Args:
        query:       Natural language query e.g. "best street food Jaipur"
        top_k:       Number of results to return
        city_filter: Optional city name to filter results (case-insensitive)

    Returns:
        List of dicts with destination, category, rating, combined_text, score
    """
    _load_index()

    query_vector = _embed_query(query)
    distances, indices = _index.search(query_vector, top_k * 3)  # fetch 3x, filter down

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue

        doc = _metadata[idx]

        # Apply city filter if provided
        if city_filter:
            if city_filter.lower() not in doc["destination"].lower():
                continue

        results.append({
            "destination": doc["destination"],
            "category": doc["category"],
            "rating": doc["rating"],
            "combined_text": doc["combined_text"],
            "score": float(dist),  # L2 distance — lower = more relevant
        })

        if len(results) >= top_k:
            break

    logger.debug(f"FAISS search '{query}' → {len(results)} results (filter: {city_filter})")
    return results


def search_by_city_and_category(city: str, category: str, top_k: int = 5) -> list[dict]:
    """
    Convenience wrapper — search by city + category combination.
    Used by AttractionTool.
    """
    query = f"best {category} in {city} attractions experiences"
    return search(query=query, top_k=top_k, city_filter=city)


def is_index_loaded() -> bool:
    """Health check — used by /health endpoint."""
    try:
        _load_index()
        return True
    except FileNotFoundError:
        return False