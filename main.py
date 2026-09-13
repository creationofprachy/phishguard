"""
PhishGuard FastAPI application.

Serves:
  - GET  /                 -> dashboard (static/index.html)
  - POST /api/predict      -> analyze a single URL
  - GET  /api/history      -> in-memory session history of analyzed URLs
  - DELETE /api/history    -> clear history
  - GET  /api/metrics      -> model evaluation metrics (from training)
  - GET  /api/health       -> liveness/readiness check
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator

from src.predict import ModelNotTrainedError, get_model_metrics, predict_url

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

app = FastAPI(
    title="PhishGuard API",
    description="Defensive, ML-based phishing URL detection service.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory history for the demo dashboard. Not persisted across
# restarts by design -- this is a local analysis tool, not a data store.
_HISTORY: List[dict] = []
_MAX_HISTORY = 100


class URLRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def url_must_be_reasonable(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("URL must not be empty")
        if len(v) > 2048:
            raise ValueError("URL is too long (max 2048 characters)")
        if any(ch.isspace() for ch in v):
            raise ValueError("URL must not contain whitespace")
        return v


@app.get("/api/health")
def health():
    try:
        get_model_metrics()
        return {"status": "ok", "model_loaded": True}
    except Exception:
        return {"status": "degraded", "model_loaded": False}


@app.get("/api/metrics")
def metrics():
    data = get_model_metrics()
    if not data:
        raise HTTPException(status_code=503, detail="Model metrics not available yet.")
    return data


@app.post("/api/predict")
def predict(payload: URLRequest):
    try:
        result = predict_url(payload.url)
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001 - defensive: never leak stack traces
        raise HTTPException(status_code=500, detail="Failed to analyze URL.") from exc

    record = {
        "url": result["url"],
        "verdict": result["verdict"],
        "risk_score": result["risk_score"],
        "confidence": result["confidence"],
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }
    _HISTORY.insert(0, record)
    del _HISTORY[_MAX_HISTORY:]

    return result


@app.get("/api/history")
def history():
    return {"count": len(_HISTORY), "items": _HISTORY}


@app.delete("/api/history")
def clear_history():
    _HISTORY.clear()
    return {"status": "cleared"}


# --- Static dashboard ---
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_dashboard():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found.")
    return FileResponse(index_path)
