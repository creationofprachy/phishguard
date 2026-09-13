"""
Inference layer used by both the FastAPI app and tests.

Loads the trained model/scaler once and exposes `predict_url`, which turns a
raw URL string into a risk score, verdict, and a short list of the features
that most influenced the decision (for the dashboard's explanation panel).
"""

import json
from functools import lru_cache

import joblib
import numpy as np

from src.config import (
    FEATURE_IMPORTANCE_PATH,
    METRICS_PATH,
    MODEL_PATH,
    SCALER_PATH,
    URL_ONLY_FEATURES,
)
from src.features import extract_features

HIGH_RISK_THRESHOLD = 0.70
MEDIUM_RISK_THRESHOLD = 0.40


class ModelNotTrainedError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _load_artifacts():
    if not MODEL_PATH.exists() or not SCALER_PATH.exists():
        raise ModelNotTrainedError(
            "Model artifacts not found. Run `python -m src.train` first."
        )
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    importance = {}
    if FEATURE_IMPORTANCE_PATH.exists():
        with open(FEATURE_IMPORTANCE_PATH) as f:
            importance = json.load(f)
    return model, scaler, importance


def _verdict_for(score: float) -> str:
    if score >= HIGH_RISK_THRESHOLD:
        return "Phishing"
    if score >= MEDIUM_RISK_THRESHOLD:
        return "Suspicious"
    return "Legitimate"


def _top_contributors(features: dict, importance: dict, top_n: int = 5):
    """Rank features that both matter to the model AND are actually
    "active"/non-trivial for this URL, as a lightweight explanation."""
    scored = []
    for name, value in features.items():
        weight = importance.get(name, 0.0)
        # Treat any non-zero / above-typical value as "contributing".
        activity = abs(value) if isinstance(value, (int, float)) else 0
        scored.append((name, value, weight, weight * (1 + activity)))
    scored.sort(key=lambda x: -x[3])
    return [
        {"feature": name, "value": value, "importance": round(weight, 5)}
        for name, value, weight, _ in scored[:top_n]
    ]


def predict_url(url: str) -> dict:
    model, scaler, importance = _load_artifacts()

    features = extract_features(url)
    vector = np.array([[features[name] for name in URL_ONLY_FEATURES]])
    vector_scaled = scaler.transform(vector)

    proba = model.predict_proba(vector_scaled)[0]
    phishing_score = float(proba[1])
    verdict = _verdict_for(phishing_score)
    top_contributors = _top_contributors(features, importance)

    return {
        "url": url,
        "verdict": verdict,
        "risk_score": round(phishing_score * 100, 2),
        "confidence": round(max(proba) * 100, 2),
        "features": features,
        "top_contributors": top_contributors,
    }


def get_model_metrics() -> dict:
    if not METRICS_PATH.exists():
        return {}
    with open(METRICS_PATH) as f:
        return json.load(f)
