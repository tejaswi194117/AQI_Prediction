"""FastAPI application for next-day PM2.5 predictions."""

from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from prediction_service import prediction_from_features


MODEL_FILE = Path("models/pm25_next_day_model.joblib")
app = FastAPI(title="Delhi AQI Prediction API", version="0.1.0")


class PredictionRequest(BaseModel):
    features: Dict[str, Optional[float]] = Field(
        ..., description="Feature values using names returned by /model-info."
    )


class PredictionResponse(BaseModel):
    model_name: str
    predicted_pm25_next_day: float
    predicted_aqi_category: str
    missing_features: List[str]


def load_artifact():
    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            "No trained model is available. Complete the historical backfill and run "
            "src/models/train_pm25_model.py first."
        )
    from joblib import load

    return load(MODEL_FILE)


@app.get("/health")
def health():
    return {"status": "ok", "model_ready": MODEL_FILE.exists()}


@app.get("/model-info")
def model_info():
    try:
        artifact = load_artifact()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {
        "model_name": artifact["model_name"],
        "target": artifact["target"],
        "feature_columns": artifact["feature_columns"],
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    try:
        artifact = load_artifact()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return prediction_from_features(artifact, request.features)
