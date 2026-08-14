"""Databricks Model Serving helpers."""

from __future__ import annotations

from typing import Any

from databricks.sdk import WorkspaceClient

ENDPOINTS = {
    "churn": "churn-xgboost",
    "deposit": "deposit-propensity-xgboost",
    "fraud": "fraud-xgb-behavioral",
}

_client: WorkspaceClient | None = None


def get_workspace_client() -> WorkspaceClient:
    """Lazy-init WorkspaceClient so import works without Databricks creds (e.g. health checks)."""
    global _client
    if _client is None:
        _client = WorkspaceClient()
    return _client


def score_model(endpoint_name: str, dataframe_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Score a model via Databricks Model Serving using SDK OAuth auth."""
    client = get_workspace_client()
    response = client.serving_endpoints.query(
        name=endpoint_name,
        dataframe_records=dataframe_records,
    )
    return response.as_dict()
