"""Wrap the saved TF-IDF + Logistic Regression category model."""

from functools import lru_cache
from pathlib import Path

import joblib

from text_norm import fold_tr

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"


@lru_cache(maxsize=1)
def _artifacts():
    vectorizer_path = MODELS_DIR / "tfidf_vectorizer.joblib"
    model_path = MODELS_DIR / "logreg_model.joblib"
    if not vectorizer_path.exists() or not model_path.exists():
        return None, None
    return joblib.load(vectorizer_path), joblib.load(model_path)


def model_available() -> bool:
    vectorizer, model = _artifacts()
    return vectorizer is not None and model is not None


def predict_category(text: str, top_k: int = 3) -> dict:
    """Return category, confidence, and top-k alternatives."""
    vectorizer, model = _artifacts()
    cleaned = " ".join(fold_tr(text or "").split())
    if not cleaned or vectorizer is None or model is None:
        return {
            "category": "Unknown",
            "confidence": 0.0,
            "top": [],
        }

    X = vectorizer.transform([cleaned])
    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    ranked = sorted(zip(model.classes_, proba), key=lambda x: x[1], reverse=True)
    return {
        "category": str(pred),
        "confidence": float(max(proba)),
        "top": [(str(label), float(score)) for label, score in ranked[:top_k]],
    }
