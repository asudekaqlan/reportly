"""ITSM leaf classifier: TF-IDF + logistic regression on süreç ids."""

from functools import lru_cache
from pathlib import Path

import joblib

from text_norm import fold_tr

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
VECTORIZER_PATH = MODELS_DIR / "itsm_tfidf.joblib"
MODEL_PATH = MODELS_DIR / "itsm_logreg.joblib"

MIN_CONFIDENCE = 0.32


@lru_cache(maxsize=1)
def _artifacts():
    if not VECTORIZER_PATH.exists() or not MODEL_PATH.exists():
        return None, None
    return joblib.load(VECTORIZER_PATH), joblib.load(MODEL_PATH)


def model_available() -> bool:
    vectorizer, model = _artifacts()
    return vectorizer is not None and model is not None


def predict_surec(text: str) -> dict:
    """Predict taxonomy surec id. Empty surec if model missing or low confidence."""
    vectorizer, model = _artifacts()
    cleaned = " ".join(fold_tr(text or "").split())
    if not cleaned or vectorizer is None or model is None:
        return {"surec": "", "confidence": 0.0, "top": []}
    matrix = vectorizer.transform([cleaned])
    proba = model.predict_proba(matrix)[0]
    ranked = sorted(zip(model.classes_, proba), key=lambda item: item[1], reverse=True)
    surec, confidence = ranked[0]
    if float(confidence) < MIN_CONFIDENCE:
        return {
            "surec": "",
            "confidence": float(confidence),
            "top": [(str(label), float(score)) for label, score in ranked[:3]],
        }
    return {
        "surec": str(surec),
        "confidence": float(confidence),
        "top": [(str(label), float(score)) for label, score in ranked[:3]],
    }
