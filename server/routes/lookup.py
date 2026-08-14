"""Customer lookup API — profile + precomputed scores + live fraud scoring."""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from server.lib.databricks import ENDPOINTS, score_model
from server.lib.features import extract_prediction
from server.lib.sql import (
    coerce_bool,
    coerce_float,
    coerce_int,
    run_sql,
    validate_customer_id,
)
from server.lib.story import generate_customer_story
from server.models import (
    CustomerLookupResponse,
    CustomerOption,
    CustomerProfile,
    LookupChurnResult,
    LookupDepositResult,
    LookupFraudResult,
)

router = APIRouter(prefix="/api/lookup", tags=["lookup"])

FRAUD_THRESHOLD = 0.9923
_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9 _.'-]{1,80}$")


def _display_name(name: Any, customer_id: str) -> str:
    cleaned = str(name or "").strip()
    return cleaned if cleaned else "Unknown"


def _customer_label(name: str, customer_id: str) -> str:
    return f"{name} ({customer_id})"


def _get_customer_name(request: Request, customer_id: str) -> str:
    rows = run_sql(
        request,
        f"""
        SELECT concat_ws(' ', any_value(t.first), any_value(t.last)) AS customer_name
        FROM internship2026.team2.card_accounts a
        LEFT JOIN internship2026.team2.card_transactions t ON a.cc_num = t.cc_num
        WHERE a.customer_id = '{customer_id}'
        GROUP BY a.customer_id
        """,
    )
    if not rows:
        return "Unknown"
    return _display_name(rows[0].get("customer_name"), customer_id)


def _resolve_customer_id(request: Request, query: str) -> str:
    """Accept a customer ID or exact/partial name and return a customer_id."""
    cleaned = query.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Enter a customer ID or name.")
    if not _SAFE_TOKEN.match(cleaned):
        raise HTTPException(status_code=400, detail="Invalid customer ID or name.")

    # Direct ID match
    if re.match(r"^C\d+$", cleaned, flags=re.IGNORECASE):
        return validate_customer_id(cleaned.upper() if cleaned[0] in "cC" else cleaned)

    # Name search (prefer exact full-name match, else first hit)
    escaped = cleaned.replace("'", "''")
    rows = run_sql(
        request,
        f"""
        WITH names AS (
          SELECT a.customer_id,
                 concat_ws(' ', any_value(t.first), any_value(t.last)) AS customer_name
          FROM internship2026.team2.card_accounts a
          INNER JOIN internship2026.team2.card_transactions t ON a.cc_num = t.cc_num
          GROUP BY a.customer_id
        )
        SELECT customer_id, customer_name
        FROM names
        WHERE lower(customer_name) = lower('{escaped}')
           OR lower(customer_name) LIKE lower('%{escaped}%')
           OR lower(customer_id) = lower('{escaped}')
        ORDER BY
          CASE WHEN lower(customer_name) = lower('{escaped}') THEN 0 ELSE 1 END,
          customer_id
        LIMIT 1
        """,
    )
    if not rows:
        # Maybe they typed an ID that isn't C-prefixed pattern we already handled
        try:
            return validate_customer_id(cleaned)
        except HTTPException as exc:
            raise HTTPException(
                status_code=404,
                detail=f"No customer found for `{cleaned}`.",
            ) from exc
    return str(rows[0]["customer_id"])


def _get_customer_profile(request: Request, customer_id: str) -> dict[str, Any] | None:
    rows = run_sql(
        request,
        f"""
        SELECT customer_id, age, gender, state, education, marital, engagement_segment, profile
        FROM internship2026.team2.customer_dimension_silver
        WHERE customer_id = '{customer_id}'
        LIMIT 1
        """,
    )
    return rows[0] if rows else None


def _get_churn(request: Request, customer_id: str) -> LookupChurnResult | None:
    rows = run_sql(
        request,
        f"""
        SELECT churn_probability, churn_risk_band, decision_threshold
        FROM internship2026.team2.churn_predictions_v1
        WHERE customer_id = '{customer_id}'
        LIMIT 1
        """,
    )
    if not rows:
        return None
    row = rows[0]
    return LookupChurnResult(
        churn_probability=coerce_float(row.get("churn_probability")),
        churn_risk_band=str(row.get("churn_risk_band") or "N/A"),
        decision_threshold=coerce_float(row.get("decision_threshold")),
    )


def _get_deposit(request: Request, customer_id: str) -> LookupDepositResult | None:
    rows = run_sql(
        request,
        f"""
        SELECT deposit_propensity, propensity_percentile, priority_band,
               campaign_eligible, recommended_for_campaign
        FROM internship2026.team2.deposit_propensity_predictions_v1
        WHERE customer_id = '{customer_id}'
        LIMIT 1
        """,
    )
    if not rows:
        return None
    row = rows[0]
    return LookupDepositResult(
        deposit_propensity=coerce_float(row.get("deposit_propensity")),
        propensity_percentile=coerce_float(row.get("propensity_percentile")),
        priority_band=str(row.get("priority_band") or "N/A"),
        campaign_eligible=coerce_bool(row.get("campaign_eligible")),
        recommended_for_campaign=coerce_bool(row.get("recommended_for_campaign")),
    )


def _get_fraud_features(request: Request, customer_id: str) -> dict[str, Any] | None:
    rows = run_sql(
        request,
        f"""
        WITH max_ts AS (
            SELECT MAX(txn_ts) as latest_ts
            FROM internship2026.team2.fraud_features_table
            WHERE customer_id = '{customer_id}'
        ),
        latest_txn AS (
            SELECT f.*, ROW_NUMBER() OVER (ORDER BY f.txn_ts DESC) as rn
            FROM internship2026.team2.fraud_features_table f
            WHERE f.customer_id = '{customer_id}'
        ),
        velocities AS (
            SELECT
                COUNT(CASE WHEN f.txn_ts >= m.latest_ts - INTERVAL 1 HOUR THEN 1 END) as cust_velocity_1h,
                COUNT(CASE WHEN f.txn_ts >= m.latest_ts - INTERVAL 24 HOURS THEN 1 END) as cust_velocity_24h,
                COUNT(CASE WHEN f.txn_ts >= m.latest_ts - INTERVAL 7 DAYS THEN 1 END) as cust_velocity_7d
            FROM internship2026.team2.fraud_features_table f
            CROSS JOIN max_ts m
            WHERE f.customer_id = '{customer_id}'
        )
        SELECT
            l.amt, l.log_amt, l.amt_ratio, l.amt_zscore,
            l.cust_avg_amt, l.cust_std_amt,
            v.cust_velocity_1h, v.cust_velocity_24h, v.cust_velocity_7d,
            l.trans_date, l.category, l.merchant
        FROM latest_txn l
        CROSS JOIN velocities v
        WHERE l.rn = 1
        """,
    )
    return rows[0] if rows else None


def _score_fraud(features: dict[str, Any]) -> LookupFraudResult:
    endpoint = ENDPOINTS["fraud"]
    payload = [
        {
            "amt": coerce_float(features.get("amt")),
            "log_amt": coerce_float(features.get("log_amt")),
            "amt_ratio": coerce_float(features.get("amt_ratio")),
            "amt_zscore": coerce_float(features.get("amt_zscore")),
            "cust_avg_amt": coerce_float(features.get("cust_avg_amt")),
            "cust_std_amt": coerce_float(features.get("cust_std_amt")),
            "cust_velocity_1h": coerce_int(features.get("cust_velocity_1h")),
            "cust_velocity_24h": coerce_int(features.get("cust_velocity_24h")),
            "cust_velocity_7d": coerce_int(features.get("cust_velocity_7d")),
        }
    ]
    try:
        result = score_model(endpoint, payload)
        fraud_score = extract_prediction(result)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Error scoring {endpoint}: {exc}") from exc

    if fraud_score > FRAUD_THRESHOLD:
        risk_level = "high"
        message = f"FRAUD ALERT (threshold: {FRAUD_THRESHOLD:.2%})"
    elif fraud_score > 0.5:
        risk_level = "info"
        message = "Elevated fraud risk"
    else:
        risk_level = "low"
        message = "Transaction appears legitimate"

    return LookupFraudResult(
        fraud_score=fraud_score,
        threshold=FRAUD_THRESHOLD,
        risk_level=risk_level,  # type: ignore[arg-type]
        message=message,
        amt=coerce_float(features.get("amt")),
        category=str(features.get("category") or "N/A"),
        merchant=str(features.get("merchant") or "N/A"),
        trans_date=str(features.get("trans_date") or "N/A"),
        cust_velocity_24h=coerce_int(features.get("cust_velocity_24h")),
        amt_zscore=coerce_float(features.get("amt_zscore")),
        endpoint=endpoint,
    )


@router.get("/options", response_model=list[CustomerOption])
def list_customer_options(request: Request) -> list[CustomerOption]:
    """Return only customers that have a real name in card transactions."""
    rows = run_sql(
        request,
        """
        WITH names AS (
          SELECT a.customer_id,
                 trim(concat_ws(' ', any_value(t.first), any_value(t.last))) AS customer_name
          FROM internship2026.team2.card_accounts a
          INNER JOIN internship2026.team2.card_transactions t ON a.cc_num = t.cc_num
          GROUP BY a.customer_id
        )
        SELECT n.customer_id, n.customer_name
        FROM names n
        INNER JOIN internship2026.team2.customer_dimension_silver c
          ON c.customer_id = n.customer_id
        WHERE n.customer_name IS NOT NULL
          AND n.customer_name != ''
          AND lower(n.customer_name) != 'unknown'
        ORDER BY n.customer_id
        """,
    )
    options: list[CustomerOption] = []
    for row in rows:
        cid = str(row.get("customer_id") or "")
        name = str(row.get("customer_name") or "").strip()
        if not cid or not name or name.lower() == "unknown":
            continue
        options.append(
            CustomerOption(
                customer_id=cid,
                customer_name=name,
                label=_customer_label(name, cid),
            )
        )
    return options


@router.get("/search", response_model=CustomerLookupResponse)
def lookup_by_query(
    request: Request,
    q: str = Query(..., min_length=1, description="Customer ID or name"),
) -> CustomerLookupResponse:
    customer_id = _resolve_customer_id(request, q)
    return lookup_customer(customer_id, request)


@router.get("/{customer_id}", response_model=CustomerLookupResponse)
def lookup_customer(customer_id: str, request: Request) -> CustomerLookupResponse:
    # Allow either raw ID or a "Name (C000033)" label pasted into the path
    raw = customer_id.strip()
    match = re.search(r"\((C\d+)\)\s*$", raw, flags=re.IGNORECASE)
    if match:
        cid = validate_customer_id(match.group(1))
    elif re.match(r"^C\d+$", raw, flags=re.IGNORECASE):
        cid = validate_customer_id(raw)
    else:
        cid = _resolve_customer_id(request, raw)

    profile_row = _get_customer_profile(request, cid)
    if not profile_row:
        raise HTTPException(status_code=404, detail=f"Customer ID `{cid}` not found in the system.")

    name = _get_customer_name(request, cid)
    profile = CustomerProfile(
        customer_id=str(profile_row.get("customer_id") or cid),
        customer_name=name,
        age=coerce_int(profile_row.get("age")) if profile_row.get("age") not in (None, "") else None,
        gender=str(profile_row.get("gender") or "N/A"),
        state=str(profile_row.get("state") or "N/A"),
        education=str(profile_row.get("education") or "N/A"),
        marital=str(profile_row.get("marital") or "N/A"),
        engagement_segment=str(profile_row.get("engagement_segment") or "N/A"),
        profile=str(profile_row.get("profile") or "N/A"),
    )

    churn = _get_churn(request, cid)
    deposit = _get_deposit(request, cid)

    fraud: LookupFraudResult | None = None
    fraud_features = _get_fraud_features(request, cid)
    if fraud_features:
        fraud = _score_fraud(fraud_features)

    response = CustomerLookupResponse(
        profile=profile,
        churn=churn,
        deposit=deposit,
        fraud=fraud,
        story=None,
    )
    response.story = generate_customer_story(request, response)
    return response

