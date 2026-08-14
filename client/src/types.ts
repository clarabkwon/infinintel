export type RiskLevel = "high" | "low" | "info";

export interface ScoreResponse {
  prediction: number;
  message: string;
  risk_level: RiskLevel;
  threshold: number | null;
  endpoint: string;
}

export interface AppConfig {
  auth: string;
  endpoints: {
    churn: string;
    deposit: string;
    fraud: string;
  };
}

export type TabId = "lookup" | "churn" | "deposit" | "fraud";

export interface CustomerProfile {
  customer_id: string;
  customer_name: string;
  age: number | null;
  gender: string;
  state: string;
  education: string;
  marital: string;
  engagement_segment: string;
  profile: string;
}

export interface CustomerOption {
  customer_id: string;
  customer_name: string;
  label: string;
}

export interface LookupChurnResult {
  churn_probability: number;
  churn_risk_band: string;
  decision_threshold: number;
}

export interface LookupDepositResult {
  deposit_propensity: number;
  propensity_percentile: number;
  priority_band: string;
  campaign_eligible: boolean | null;
  recommended_for_campaign: boolean | null;
}

export interface LookupFraudResult {
  fraud_score: number;
  threshold: number;
  risk_level: RiskLevel;
  message: string;
  amt: number;
  category: string;
  merchant: string;
  trans_date: string;
  cust_velocity_24h: number;
  amt_zscore: number;
  endpoint: string;
}

export interface CustomerLookupResponse {
  profile: CustomerProfile;
  churn: LookupChurnResult | null;
  deposit: LookupDepositResult | null;
  fraud: LookupFraudResult | null;
  story: string | null;
}
