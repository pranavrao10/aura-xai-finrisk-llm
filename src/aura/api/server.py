from __future__ import annotations
import os
import traceback
from typing import Literal, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from aura.app.config import (
    ui_features,
    validate_ui_payload,
    InputError,
)
from aura.models.predict import predict_with_explanations
from aura.explain.explainer import generate_explanation


class ApplicantPayload(BaseModel):
    grade: str = Field(..., description="Letter A-G")
    term: int = Field(..., description="36 or 60")
    acc_open_past_24mths: int = Field(..., ge=0)
    dti: float = Field(..., ge=0)
    fico_mid: int = Field(..., ge=300, le=850)

    @field_validator("grade")
    def grade_upper(cls, v):
        return v.strip().upper()

class PredictResponse(BaseModel):
    prob_default: float
    threshold: float
    threshold_policy: str
    threshold_delta: float
    risk_class: Literal["High","Low"]
    near_threshold_flag: bool
    model_version: str
    top_local_reasons: Optional[list[dict]] = None

class ExplainResponse(BaseModel):
    narrative: str

class PredictExplainResponse(BaseModel):
    prediction: PredictResponse
    explanation: ExplainResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        dummy = {
            "grade": "B", "term": 36,
            "acc_open_past_24mths": 1,
            "dti": 10.0, "fico_mid": 700
        }
        _ = predict_with_explanations(dummy, max_reasons=5)
    except Exception as e:
        print("Warm-up failed:", e)
    yield

app = FastAPI(title="AURA - Autonomous Credit Risk Assessment", version="1.0.0", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(InputError)
async def input_error_handler(request: Request, exc: InputError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.post("/predict", response_model=PredictResponse)
def predict(payload: ApplicantPayload):
    try:
        cleaned = validate_ui_payload(payload.dict(), require_all=True)
    except InputError as e:
        raise HTTPException(status_code=422, detail=str(e))
    bundle = predict_with_explanations(cleaned, max_reasons=5)

    near_flag = abs(bundle["threshold_delta"]) <= bundle["near_threshold_band"]
    return PredictResponse(
        prob_default=bundle["prob_default"],
        threshold=bundle["threshold"],
        threshold_policy=bundle["threshold_policy"],
        threshold_delta=bundle["threshold_delta"],
        risk_class=bundle["risk_class"],
        near_threshold_flag=near_flag,
        model_version=bundle["model_version"],
        top_local_reasons=bundle["top_local_shap"]
    )

@app.post("/explain", response_model=ExplainResponse)
def explain(payload: ApplicantPayload):
    cleaned = validate_ui_payload(payload.dict(), require_all=True)
    bundle = predict_with_explanations(cleaned, max_reasons=5)
    try:
        out = generate_explanation(bundle)
        return ExplainResponse(narrative=out["narrative"])
    except Exception:
        fallback = (
            "Explanation unavailable due to a system error. "
            "Probability and Classification have been provided. "
            "Please review manually."
        )
        return ExplainResponse(narrative=fallback)

@app.post("/predict_explain", response_model=PredictExplainResponse)
def predict_explain(payload: ApplicantPayload):
    cleaned = validate_ui_payload(payload.dict(), require_all=True)
    bundle = predict_with_explanations(cleaned, max_reasons=5)

    try:
        explanation = generate_explanation(bundle)["narrative"]
    except Exception:
        explanation = (
            "Explanation unavailable due to a system error. "
            "Please review probabilities and factors manually."
        )

    near_flag = abs(bundle["threshold_delta"]) <= bundle["near_threshold_band"]
    pred_resp = PredictResponse(
        prob_default=bundle["prob_default"],
        threshold=bundle["threshold"],
        threshold_policy=bundle["threshold_policy"],
        threshold_delta=bundle["threshold_delta"],
        risk_class=bundle["risk_class"],
        near_threshold_flag=near_flag,
        model_version=bundle["model_version"],
        top_local_reasons=bundle["top_local_shap"]
    )
    return PredictExplainResponse(
        prediction=pred_resp,
        explanation=ExplainResponse(narrative=explanation)
    )