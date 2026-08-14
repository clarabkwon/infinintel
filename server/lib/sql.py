"""SQL helpers for customer lookup (user OBO token when available)."""

from __future__ import annotations

import os
import re
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.config import Config
from databricks.sdk.service.sql import StatementState
from fastapi import HTTPException, Request

from server.lib.databricks import get_workspace_client

WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "3209b068f2f52860")
CUSTOMER_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def validate_customer_id(customer_id: str) -> str:
    cleaned = customer_id.strip()
    if not cleaned or not CUSTOMER_ID_RE.match(cleaned):
        raise HTTPException(
            status_code=400,
            detail="Invalid customer ID. Use letters, numbers, underscores, or hyphens only.",
        )
    return cleaned


def _client_for_request(request: Request) -> WorkspaceClient:
    """Prefer user OBO token (Databricks Apps); fall back to app/SP credentials locally."""
    token = request.headers.get("x-forwarded-access-token")
    host = os.getenv("DATABRICKS_HOST")
    if token and host:
        return WorkspaceClient(config=Config(host=host, token=token, auth_type="pat"))
    return get_workspace_client()


def run_sql(request: Request, query: str) -> list[dict[str, Any]]:
    """Execute SQL via statement execution API; return list of row dicts."""
    client = _client_for_request(request)
    try:
        result = client.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID,
            statement=query,
            wait_timeout="50s",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"SQL Error: {exc}") from exc

    if result.status is None or result.status.state != StatementState.SUCCEEDED:
        error_msg = (
            result.status.error.message
            if result.status and result.status.error
            else "Unknown SQL error"
        )
        raise HTTPException(status_code=502, detail=f"SQL Error: {error_msg}")

    if not result.manifest or not result.manifest.schema or not result.manifest.schema.columns:
        return []

    columns = [col.name for col in result.manifest.schema.columns]
    rows = result.result.data_array if result.result and result.result.data_array else []
    return [dict(zip(columns, row, strict=False)) for row in rows]


def coerce_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def coerce_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def coerce_bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes"}
