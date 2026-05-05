import pandas as pd
from pathlib import Path
from loguru import logger

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "travel_reviews.csv"

# UCI Travel Reviews — 10 category mapping
CATEGORY_MAP = {
    "Category 1":  "Art Galleries",
    "Category 2":  "Dance Clubs",
    "Category 3":  "Juice Bars",
    "Category 4":  "Restaurants",
    "Category 5":  "Museums",
    "Category 6":  "Resorts",
    "Category 7":  "Parks and Picnic Spots",
    "Category 8":  "Beaches",
    "Category 9":  "Theaters",
    "Category 10": "Religious Institutions",
}

# Simulated destinations — UCI dataset has no location column
# We distribute users across Indian destinations for our RAG
DESTINATION_CYCLE = [
    "Jaipur", "Jodhpur", "Udaipur", "Jaisalmer",
    "Kerala", "Goa", "Mumbai", "Delhi", "Manali", "Agra",
]


def load_travel_reviews() -> list[dict]:
    """
    Load and preprocess UCI travel reviews CSV.
    Returns list of dicts with combined_text ready for embedding.
    """
    if not DATA_PATH.exists():
        logger.error(f"Dataset not found at {DATA_PATH}")
        raise FileNotFoundError(f"travel_reviews.csv not found at {DATA_PATH}")

    logger.info(f"Loading travel reviews from {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    logger.info(f"Raw dataset shape: {df.shape}")
    logger.info(f"Columns: {df.columns.tolist()}")

    df = df.fillna(0)
    logger.info(f"Processing {len(df)} user review rows...")

    documents = []
    for idx, row in df.iterrows():
        # Assign destination cyclically — spreads reviews across Indian cities
        destination = DESTINATION_CYCLE[idx % len(DESTINATION_CYCLE)]

        # Find top 3 rated categories for this user
        category_scores = {
            CATEGORY_MAP[col]: float(row[col])
            for col in CATEGORY_MAP
            if col in row.index
        }
        top_categories = sorted(
            category_scores.items(), key=lambda x: x[1], reverse=True
        )[:3]

        # Overall rating — average of all categories
        all_scores = list(category_scores.values())
        overall_rating = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0

        combined_text = _build_combined_text(
            destination=destination,
            top_categories=top_categories,
            category_scores=category_scores,
            overall_rating=overall_rating,
        )

        documents.append({
            "combined_text": combined_text,
            "destination":   destination,
            "category":      top_categories[0][0] if top_categories else "General",
            "rating":        str(overall_rating),
        })

    logger.info(f"Built {len(documents)} documents for embedding")
    return documents


def _build_combined_text(
    destination: str,
    top_categories: list,
    category_scores: dict,
    overall_rating: float,
) -> str:
    top_str = ", ".join(
        f"{cat} ({score:.1f}/4)" for cat, score in top_categories
    )
    all_str = ". ".join(
        f"{cat}: {score:.1f}" for cat, score in category_scores.items()
    )
    return (
        f"Destination: {destination}. "
        f"Top experiences: {top_str}. "
        f"Overall rating: {overall_rating}/4. "
        f"Category ratings: {all_str}."
    )