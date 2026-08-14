"""Scoring API routes for churn, deposit, and fraud models."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from server.lib.databricks import ENDPOINTS, score_model
from server.lib.features import (
    build_churn_record,
    build_deposit_record,
    build_fraud_record,
    extract_prediction,
)
from server.lib.proba import score_probability
from server.models import ChurnRequest, DepositRequest, FraudRequest, ScoreResponse

router = APIRouter(prefix="/api/score", tags=["score"])

CHURN_THRESHOLD = 0.5
DEPOSIT_THRESHOLD = 0.5
FRAUD_THRESHOLD = 0.9923


@router.post("/churn", response_model=ScoreResponse)
def score_churn(body: ChurnRequest) -> ScoreResponse:
    endpoint = ENDPOINTS["churn"]
    try:
        prediction = score_probability(endpoint, "churn", build_churn_record(body))
    except Exception as exc:  # noqa: BLE001 — surface Serving errors to the client
        raise HTTPException(status_code=502, detail=f"Error scoring {endpoint}: {exc}") from exc

    high_risk = prediction > CHURN_THRESHOLD
    return ScoreResponse(
        prediction=prediction,
        threshold=CHURN_THRESHOLD,
        endpoint=endpoint,
        risk_level="high" if high_risk else "low",
        message=(
            "HIGH CHURN RISK — Consider retention intervention."
            if high_risk
            else "Low churn risk."
        ),
    )


@router.post("/deposit", response_model=ScoreResponse)
def score_deposit(body: DepositRequest) -> ScoreResponse:
    endpoint = ENDPOINTS["deposit"]
    try:
        prediction = score_probability(endpoint, "deposit", build_deposit_record(body))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Error scoring {endpoint}: {exc}") from exc

    high = prediction > DEPOSIT_THRESHOLD
    return ScoreResponse(
        prediction=prediction,
        threshold=DEPOSIT_THRESHOLD,
        endpoint=endpoint,
        risk_level="high" if high else "info",
        message=(
            "HIGH propensity — Good candidate for deposit marketing."
            if high
            else "Lower propensity — May need nurturing."
        ),
    )


@router.post("/fraud", response_model=ScoreResponse)
def score_fraud(body: FraudRequest) -> ScoreResponse:
    endpoint = ENDPOINTS["fraud"]
    try:
        result = score_model(endpoint, [build_fraud_record(body)])
        prediction = extract_prediction(result)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Error scoring {endpoint}: {exc}") from exc

    alert = prediction > FRAUD_THRESHOLD
    return ScoreResponse(
        prediction=prediction,
        threshold=FRAUD_THRESHOLD,
        endpoint=endpoint,
        risk_level="high" if alert else "low",
        message=(
            f"FRAUD ALERT — Score exceeds threshold ({FRAUD_THRESHOLD:.2%})."
            if alert
            else "Transaction appears legitimate."
        ),
    )
