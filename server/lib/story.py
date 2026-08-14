"""Generate stakeholder customer narratives from live lookup facts via Foundation Models."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from fastapi import Request

from server.lib.databricks import get_workspace_client
from server.lib.sql import coerce_float, run_sql
from server.models import CustomerLookupResponse

logger = logging.getLogger(__name__)

STORY_MODEL = "databricks-meta-llama-3-1-8b-instruct"


def _money(value: Any) -> str:
    amount = coerce_float(value)
    return f"${amount:,.2f}"


def _lifestyle_and_transactions(request: Request, customer_id: str) -> dict[str, Any]:
    rows = run_sql(
        request,
        f"""
        SELECT t.job, t.city AS home_city, t.state AS home_state,
               t.amt, t.category, t.merchant, t.city, t.state,
               cast(t.trans_date as string) AS trans_date
        FROM internship2026.team2.card_accounts a
        INNER JOIN internship2026.team2.card_transactions t ON a.cc_num = t.cc_num
        WHERE a.customer_id = '{customer_id}'
        ORDER BY t.amt DESC
        LIMIT 8
        """,
    )
    if not rows:
        return {}
    return {
        "job": rows[0].get("job"),
        "home_city": rows[0].get("home_city"),
        "home_state": rows[0].get("home_state"),
        "largest_historical_purchases": [
            {
                "amount": _money(r.get("amt")),
                "category": r.get("category"),
                "merchant": r.get("merchant"),
                "city": r.get("city"),
                "state": r.get("state"),
                "trans_date": r.get("trans_date"),
            }
            for r in rows
        ],
    }


def _build_facts(request: Request, lookup: CustomerLookupResponse) -> dict[str, Any]:
    profile = lookup.profile
    facts: dict[str, Any] = {
        "customer_id": profile.customer_id,
        "customer_name": profile.customer_name,
        "age": profile.age,
        "gender": profile.gender,
        "state": profile.state,
        "education": profile.education,
        "marital": profile.marital,
        "engagement_segment": profile.engagement_segment,
        "profile_segment": profile.profile,
    }
    if lookup.churn:
        facts["churn"] = {
            "probability_pct": f"{lookup.churn.churn_probability * 100:.2f}%",
            "risk_band": (lookup.churn.churn_risk_band or "").strip().lower(),
        }
    if lookup.deposit:
        facts["deposit_propensity"] = {
            "probability_pct": f"{lookup.deposit.deposit_propensity * 100:.2f}%",
            "priority_band": (lookup.deposit.priority_band or "").strip().lower(),
            "campaign_eligible": lookup.deposit.campaign_eligible,
        }
    if lookup.fraud:
        # This is the ONLY transaction used for the fraud score shown in the UI.
        facts["fraud_scored_transaction"] = {
            "probability_pct": f"{lookup.fraud.fraud_score * 100:.2f}%",
            "message": lookup.fraud.message,
            "amount": _money(lookup.fraud.amt),
            "category": lookup.fraud.category,
            "merchant": lookup.fraud.merchant,
            "velocity_24h": lookup.fraud.cust_velocity_24h,
        }

    lifestyle = _lifestyle_and_transactions(request, profile.customer_id)
    if lifestyle:
        facts["lifestyle"] = {
            "job": lifestyle.get("job"),
            "home_city": lifestyle.get("home_city"),
            "home_state": lifestyle.get("home_state"),
        }
        facts["largest_historical_purchases"] = lifestyle.get(
            "largest_historical_purchases", []
        )
    return facts


def _clean_story_text(text: str) -> str:
    """Strip meta preambles like 'Here is a concise stakeholder narrative about X.'"""
    cleaned = text.strip().strip('"').strip("'")
    # Remove a leading intro sentence that announces the narrative instead of telling it.
    cleaned = re.sub(
        r"^(here\s+is|here'?s|this\s+is|below\s+is)\s+"
        r"(a\s+)?(concise\s+)?(stakeholder\s+)?(narrative|story|summary|overview)\b"
        r"[^.!?]*[.!:]\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def generate_customer_story(request: Request, lookup: CustomerLookupResponse) -> str:
    """Ask Foundation Model to narrate THIS customer's facts for stakeholders."""
    facts = _build_facts(request, lookup)
    system = (
        "You are a banking analytics storyteller. Write a concise stakeholder narrative "
        "(3-5 sentences) about ONE specific customer using ONLY the JSON facts provided. "
        "Ground the story in their demographics, job/lifestyle if present, and how their "
        "churn, deposit propensity, and fraud signals might play out in real life. "
        "Do not invent accounts, SSNs, merchants, amounts, or other facts. "
        "Do not mention JSON or that you are an AI. "
        "CRITICAL money rule: copy dollar amounts EXACTLY as written in the facts "
        "(including cents). Never rescale, round to thousands, or merge an amount from "
        "largest_historical_purchases with a merchant from fraud_scored_transaction. "
        "When discussing fraud, use ONLY fraud_scored_transaction.amount + merchant. "
        "largest_historical_purchases are separate background context only. "
        "CRITICAL band rule: use churn.risk_band and deposit_propensity.priority_band "
        "exactly as given — do not replace them with synonyms like elevated/significant. "
        "Write band labels in normal sentence case (lowercase mid-sentence). "
        "Copy probability_pct strings exactly when quoting percentages. "
        "IMPORTANT: Start directly with the story. Do NOT begin with meta phrases like "
        "'Here is a concise stakeholder narrative about…', 'Here's a story about…', "
        "or any similar preamble. Tone: professional, vivid, useful for business stakeholders."
    )
    band_rules: list[str] = []
    if lookup.churn:
        band = (lookup.churn.churn_risk_band or "").strip().lower()
        band_rules.append(
            f'Call churn risk "{band}" '
            f"(probability {lookup.churn.churn_probability:.2%})."
        )
    if lookup.deposit:
        band = (lookup.deposit.priority_band or "").strip().lower()
        band_rules.append(
            f'Call deposit priority "{band}" '
            f"(propensity {lookup.deposit.deposit_propensity:.2%})."
        )
    if lookup.fraud:
        band_rules.append(
            "Fraud transaction amount must be written exactly as "
            f"{_money(lookup.fraud.amt)} at {lookup.fraud.merchant}."
        )
    rules_block = "\n".join(band_rules)
    user = (
        f"Write the customer story from these facts:\n{json.dumps(facts, default=str)}\n\n"
        f"Required wording (do not paraphrase amounts or band labels):\n{rules_block}"
    )
    try:
        client = get_workspace_client()
        response = client.serving_endpoints.query(
            name=STORY_MODEL,
            messages=[
                ChatMessage(role=ChatMessageRole.SYSTEM, content=system),
                ChatMessage(role=ChatMessageRole.USER, content=user),
            ],
            max_tokens=320,
            temperature=0.2,
        )
        payload = response.as_dict()
        choices = payload.get("choices") or []
        if choices:
            content = choices[0].get("message", {}).get("content")
            if content:
                return _clean_story_text(str(content))
        return "Story unavailable for this customer right now."
    except Exception as exc:  # noqa: BLE001
        logger.warning("Customer story generation failed: %s", exc)
        return (
            "Could not generate an AI story for this customer. "
            "Scores and profile details below are still available."
        )
