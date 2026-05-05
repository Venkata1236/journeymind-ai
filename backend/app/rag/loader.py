import pandas as pd
from pathlib import Path
from loguru import logger


DATA_PATH = Path(__file__).parent.parent.parent / "data" / "travel_reviews.csv"


def load_travel_reviews() -> list[dict]:
    """
    Load and preprocess travel reviews CSV.
    Returns list of dicts with combined_text ready for embedding.
    """
    if not DATA_PATH.exists():
        logger.error(f"Dataset not found at {DATA_PATH}")
        raise FileNotFoundError(f"travel_reviews.csv not found at {DATA_PATH}")

    logger.info(f"Loading travel reviews from {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    logger.info(f"Raw dataset shape: {df.shape}")
    logger.info(f"Columns: {df.columns.tolist()}")

    # Drop rows with missing critical fields
    df = df.dropna(subset=["User Location", "Category"])
    df = df.fillna("")

    logger.info(f"After cleaning: {df.shape[0]} rows")

    documents = []
    for _, row in df.iterrows():
        # Build combined text per review for embedding
        combined_text = _build_combined_text(row)
        documents.append({
            "combined_text": combined_text,
            "destination": str(row.get("User Location", "")).strip(),
            "category": str(row.get("Category", "")).strip(),
            "rating": str(row.get("Overall Rating", "")).strip(),
        })

    logger.info(f"Built {len(documents)} documents for embedding")
    return documents


def _build_combined_text(row: pd.Series) -> str:
    """
    Build a rich combined text string per review row.
    This is what gets embedded — quality here = quality retrieval.
    """
    destination = str(row.get("User Location", "")).strip()
    category = str(row.get("Category", "")).strip()
    rating = str(row.get("Overall Rating", "")).strip()

    # Collect all attribute columns (they hold numeric ratings per attribute)
    attribute_parts = []
    skip_cols = {"User", "User ID", "User Location", "Category", "Overall Rating"}
    for col in row.index:
        if col not in skip_cols:
            val = str(row[col]).strip()
            if val and val != "nan" and val != "0":
                attribute_parts.append(f"{col}: {val}")

    attributes_str = ". ".join(attribute_parts) if attribute_parts else ""

    combined = (
        f"Destination: {destination}. "
        f"Category: {category}. "
        f"Overall Rating: {rating}/5. "
        f"{attributes_str}"
    ).strip()

    return combined