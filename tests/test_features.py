"""Unit tests for derived feature builders (no Databricks credentials required)."""

from __future__ import annotations

import math

from server.lib.features import (
    build_churn_record,
    build_deposit_record,
    build_fraud_record,
    extract_prediction,
)
from server.models import ChurnRequest, DepositRequest, FraudRequest


def test_build_churn_record_includes_derived_features() -> None:
    record = build_churn_record(
        ChurnRequest(
            months_on_book=36,
            months_inactive_12m=2,
            contacts_count_12m=3,
            acct_total_relationship_count=4,
            acct_total_trans_amt=5000,
            acct_total_trans_ct=60,
            acct_total_amt_chng_q4_q1=0.8,
            acct_total_ct_chng_q4_q1=0.7,
        )
    )
    assert record["account_history_available"] == 36
    assert record["acct_transactions_per_relationship"] == 15.0
    assert record["acct_amount_per_relationship"] == 1250.0
    assert record["acct_amount_per_transaction"] == 5000 / 60
    assert record["inactive_contact_interaction"] == 6
    assert record["acct_activity_change_combined"] == 1.5
    assert len(record) == 29


def test_build_deposit_record_passthrough() -> None:
    record = build_deposit_record(DepositRequest(bank_balance=15000, education_ordinal=3))
    assert record["bank_balance"] == 15000
    assert record["education_ordinal"] == 3
    assert record["prev_outcome_encoded"] == 0


def test_build_fraud_record_computes_log1p() -> None:
    record = build_fraud_record(FraudRequest(amt=150.0))
    assert record["amt"] == 150.0
    assert record["log_amt"] == math.log1p(150.0)


def test_extract_prediction_scalar_and_dict() -> None:
    assert extract_prediction({"predictions": [0.42]}) == 0.42
    assert extract_prediction({"predictions": [{"prediction": 0.99}]}) == 0.99
    assert extract_prediction({"predictions": [{"score": 0.12}]}) == 0.12
