import json
import faiss
import numpy as np
from pathlib import Path
from loguru import logger
from openai import OpenAI
from app.core.config import get_settings
from app.rag.loader import load_travel_reviews

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)

INDEX_PATH = Path(settings.faiss_index_path)
METADATA_PATH = INDEX_PATH / "travel_metadata.json"
FAISS_FILE = INDEX_PATH / "travel.index"
EMBEDDING_MODEL = "text-embedding-ada-002"
BATCH_SIZE = 100


def _embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using OpenAI embeddings."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def build_faiss_index():
    """
    Load travel reviews → embed in batches → build FAISS index → save to disk.
    Run this once before starting the API.
    """
    INDEX_PATH.mkdir(parents=True, exist_ok=True)

    if FAISS_FILE.exists() and METADATA_PATH.exists():
        logger.info("FAISS index already exists — skipping rebuild")
        return

    logger.info("Starting FAISS index build...")
    documents = load_travel_reviews()

    texts = [doc["combined_text"] for doc in documents]
    metadata = [
        {
            "destination": doc["destination"],
            "category": doc["category"],
            "rating": doc["rating"],
            "combined_text": doc["combined_text"],
        }
        for doc in documents
    ]

    # Embed in batches to avoid OpenAI rate limits
    all_embeddings = []
    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i: i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        logger.info(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)")
        embeddings = _embed_batch(batch)
        all_embeddings.extend(embeddings)

    # Build FAISS index
    dimension = len(all_embeddings[0])
    logger.info(f"Building FAISS index — dimension: {dimension}, docs: {len(all_embeddings)}")

    index = faiss.IndexFlatL2(dimension)
    vectors = np.array(all_embeddings, dtype=np.float32)
    index.add(vectors)

    # Save index + metadata
    faiss.write_index(index, str(FAISS_FILE))
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    logger.success(f"FAISS index saved — {index.ntotal} vectors at {FAISS_FILE}")
    logger.success(f"Metadata saved at {METADATA_PATH}")


if __name__ == "__main__":
    build_faiss_index()