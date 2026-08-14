"""Derived feature builders for each scoring model."""

from __future__ import annotations

import math
from typing import Any

from server.models import ChurnRequest, DepositRequest, FraudRequest


def build_churn_record(data: ChurnRequest) -> dict[str, Any]:
    rel = max(data.acct_total_relationship_count, 1)
    trans_ct = max(data.acct_total_trans_ct, 1)
    return {
        "age": data.age,
        "gender": data.gender,
        "state": data.state,
        "education": data.education,
        "marital": data.marital,
        "profile": data.profile,
        "has_card": data.has_card,
        "has_marketing": data.has_marketing,
        "engagement_segment": data.engagement_segment,
        "card_category": data.card_category,
        "income_category": data.income_category,
        "months_on_book": data.months_on_book,
        "months_inactive_12m": data.months_inactive_12m,
        "contacts_count_12m": data.contacts_count_12m,
        "credit_limit": data.credit_limit,
        "revolving_balance": data.revolving_balance,
        "utilization_ratio": data.utilization_ratio,
        "acct_dependent_count": data.acct_dependent_count,
        "acct_total_relationship_count": data.acct_total_relationship_count,
        "acct_total_trans_amt": data.acct_total_trans_amt,
        "acct_total_trans_ct": data.acct_total_trans_ct,
        "acct_total_amt_chng_q4_q1": data.acct_total_amt_chng_q4_q1,
        "acct_total_ct_chng_q4_q1": data.acct_total_ct_chng_q4_q1,
        "account_history_available": data.months_on_book,
        "acct_transactions_per_relationship": data.acct_total_trans_ct / rel,
        "acct_amount_per_relationship": data.acct_total_trans_amt / rel,
        "acct_amount_per_transaction": data.acct_total_trans_amt / trans_ct,
        "inactive_contact_interaction": data.months_inactive_12m * data.contacts_count_12m,
        "acct_activity_change_combined": data.acct_total_amt_chng_q4_q1 + data.acct_total_ct_chng_q4_q1,
    }


def build_deposit_record(data: DepositRequest) -> dict[str, Any]:
    return {
        "age": data.age,
        "gender": data.gender,
        "state": data.state,
        "marital": data.marital,
        "profile": data.profile,
        "has_card": data.has_card,
        "has_marketing": data.has_marketing,
        "engagement_segment": data.engagement_segment,
        "has_personal_loan": data.has_personal_loan,
        "has_housing_loan": data.has_housing_loan,
        "has_credit_default": data.has_credit_default,
        "bank_balance": data.bank_balance,
        "was_previously_contacted": data.was_previously_contacted,
        "prev_outcome_encoded": data.prev_outcome_encoded,
        "education_ordinal": data.education_ordinal,
        "loan_burden_score": data.loan_burden_score,
    }


def build_fraud_record(data: FraudRequest) -> dict[str, Any]:
    return {
        "amt": data.amt,
        "log_amt": math.log1p(data.amt),
        "amt_ratio": data.amt_ratio,
        "amt_zscore": data.amt_zscore,
        "cust_avg_amt": data.cust_avg_amt,
        "cust_std_amt": data.cust_std_amt,
        "cust_velocity_1h": data.cust_velocity_1h,
        "cust_velocity_24h": data.cust_velocity_24h,
        "cust_velocity_7d": data.cust_velocity_7d,
    }


def extract_prediction(result: dict[str, Any]) -> float:
    """Normalize Serving response shapes into a single float score / probability."""
    predictions = result.get("predictions", [])
    if not predictions:
        raise ValueError("Model response contained no predictions")
    first = predictions[0]
    if isinstance(first, dict):
        value = first.get("prediction", first.get("score", first.get("probability")))
        if value is None and "probabilities" in first:
            value = first["probabilities"]
        if value is None:
            raise ValueError(f"Unexpected prediction object: {first}")
        first = value
    # Probability vector from predict_proba-style responses: [p0, p1] → positive class
    if isinstance(first, (list, tuple)) and first:
        if len(first) >= 2:
            return float(first[1])
        return float(first[0])
    return float(first)
