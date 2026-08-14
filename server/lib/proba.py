"""Local UC model scoring via predict_proba (serving endpoints return class labels only)."""

from __future__ import annotations

import logging
import threading
from typing import Any

import pandas as pd

from server.lib.databricks import score_model

logger = logging.getLogger(__name__)

_MODEL_URIS = {
    "churn": "models:/internship2026.team2.churn_xgboost/1",
    "deposit": "models:/internship2026.team2.deposit_propensity_xgboost/1",
}

_models: dict[str, Any] = {}
_load_errors: dict[str, str] = {}
_lock = threading.Lock()


def _load_model(kind: str) -> Any | None:
    if kind in _models:
        return _models[kind]
    if kind in _load_errors:
        return None

    with _lock:
        if kind in _models:
            return _models[kind]
        if kind in _load_errors:
            return None
        try:
            import mlflow

            mlflow.set_tracking_uri("databricks")
            model = mlflow.sklearn.load_model(_MODEL_URIS[kind])
            if not hasattr(model, "predict_proba"):
                raise RuntimeError(f"{kind} model does not expose predict_proba")
            _models[kind] = model
            logger.info("Loaded %s model for probability scoring", kind)
            return model
        except Exception as exc:  # noqa: BLE001
            _load_errors[kind] = str(exc)
            logger.warning("Could not load %s model for predict_proba: %s", kind, exc)
            return None


def _positive_class_probability(model: Any, record: dict[str, Any]) -> float:
    frame = pd.DataFrame([record])
    proba = model.predict_proba(frame)[0]
    classes = list(getattr(model, "classes_", [0, 1]))
    if 1 in classes:
        return float(proba[classes.index(1)])
    if True in classes:
        return float(proba[classes.index(True)])
    return float(proba[-1])


def score_probability(endpoint_name: str, kind: str, record: dict[str, Any]) -> float:
    """Return P(positive class). Prefer local predict_proba; fall back to serving."""
    model = _load_model(kind)
    if model is not None:
        return _positive_class_probability(model, record)

    # Serving endpoints for churn/deposit return class labels (0/1), not probabilities.
    logger.warning(
        "Falling back to serving for %s (predict_proba unavailable: %s)",
        kind,
        _load_errors.get(kind, "unknown"),
    )
    result = score_model(endpoint_name, [record])
    from server.lib.features import extract_prediction

    return extract_prediction(result)
