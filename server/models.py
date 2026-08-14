"""Pydantic request/response models for scoring APIs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ScoreResponse(BaseModel):
    prediction: float
    message: str
    risk_level: Literal["high", "low", "info"]
    threshold: float | None = None
    endpoint: str


class ChurnRequest(BaseModel):
    age: int = Field(45, ge=18, le=100)
    gender: Literal["M", "F"] = "M"
    state: str = "VA"
    education: Literal[
        "Uneducated",
        "High School",
        "College",
        "Graduate",
        "Post-Graduate",
        "Doctorate",
    ] = "Graduate"
    marital: Literal["Single", "Married", "Divorced", "Unknown"] = "Married"
    profile: Literal["salaried", "self_employed", "business", "other"] = "salaried"
    has_card: bool = True
    has_marketing: bool = False
    engagement_segment: Literal["active", "moderate", "inactive", "dormant"] = "active"
    card_category: Literal["Blue", "Silver", "Gold", "Platinum"] = "Blue"
    income_category: Literal[
        "Less than $40K",
        "$40K - $60K",
        "$60K - $80K",
        "$80K - $120K",
        "$120K +",
    ] = "$60K - $80K"
    months_on_book: int = Field(36, ge=1, le=60)
    months_inactive_12m: int = Field(2, ge=0, le=12)
    contacts_count_12m: int = Field(3, ge=0, le=12)
    credit_limit: float = Field(8000, ge=0, le=50000)
    revolving_balance: float = Field(1500, ge=0, le=30000)
    utilization_ratio: float = Field(0.3, ge=0, le=1)
    acct_dependent_count: int = Field(2, ge=0, le=10)
    acct_total_relationship_count: int = Field(4, ge=1, le=10)
    acct_total_trans_amt: float = Field(5000, ge=0, le=50000)
    acct_total_trans_ct: int = Field(60, ge=0, le=200)
    acct_total_amt_chng_q4_q1: float = Field(0.8, ge=0, le=3)
    acct_total_ct_chng_q4_q1: float = Field(0.7, ge=0, le=3)


class DepositRequest(BaseModel):
    age: int = Field(35, ge=18, le=100)
    gender: Literal["M", "F"] = "M"
    state: str = "MD"
    marital: Literal["Single", "Married", "Divorced", "Unknown"] = "Married"
    profile: Literal["salaried", "self_employed", "business", "other"] = "salaried"
    has_card: bool = True
    has_marketing: bool = True
    engagement_segment: Literal["active", "moderate", "inactive", "dormant"] = "active"
    has_personal_loan: Literal[0, 1] = 0
    has_housing_loan: Literal[0, 1] = 0
    has_credit_default: Literal[0, 1] = 0
    bank_balance: float = Field(15000, ge=0, le=100000)
    was_previously_contacted: Literal[0, 1] = 0
    prev_outcome_encoded: Literal[0, 1, 2] = 0
    education_ordinal: int = Field(3, ge=1, le=6)
    loan_burden_score: float = Field(2, ge=0, le=10)


class FraudRequest(BaseModel):
    amt: float = Field(150.0, ge=0, le=50000)
    amt_ratio: float = Field(1.2, ge=0, le=100)
    amt_zscore: float = Field(0.5, ge=-10, le=10)
    cust_avg_amt: float = Field(125.0, ge=0, le=50000)
    cust_std_amt: float = Field(50.0, ge=0, le=10000)
    cust_velocity_1h: int = Field(2, ge=0, le=100)
    cust_velocity_24h: int = Field(5, ge=0, le=500)
    cust_velocity_7d: int = Field(15, ge=0, le=2000)


class CustomerOption(BaseModel):
    customer_id: str
    customer_name: str
    label: str


class CustomerProfile(BaseModel):
    customer_id: str
    customer_name: str = "Unknown"
    age: int | None = None
    gender: str = "N/A"
    state: str = "N/A"
    education: str = "N/A"
    marital: str = "N/A"
    engagement_segment: str = "N/A"
    profile: str = "N/A"


class LookupChurnResult(BaseModel):
    churn_probability: float
    churn_risk_band: str
    decision_threshold: float


class LookupDepositResult(BaseModel):
    deposit_propensity: float
    propensity_percentile: float
    priority_band: str
    campaign_eligible: bool | None = None
    recommended_for_campaign: bool | None = None


class LookupFraudResult(BaseModel):
    fraud_score: float
    threshold: float
    risk_level: Literal["high", "low", "info"]
    message: str
    amt: float
    category: str
    merchant: str
    trans_date: str
    cust_velocity_24h: int
    amt_zscore: float
    endpoint: str


class CustomerLookupResponse(BaseModel):
    profile: CustomerProfile
    churn: LookupChurnResult | None = None
    deposit: LookupDepositResult | None = None
    fraud: LookupFraudResult | None = None
    story: str | None = None
