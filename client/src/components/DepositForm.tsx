import { FormEvent, useState } from "react";
import { scoreDeposit } from "../api";
import { pick, randFloat, randInt, US_STATES } from "../randomize";
import type { ScoreResponse } from "../types";
import { Field, numberHandler, stringHandler } from "./FormControls";
import { ResultCard } from "./ResultCard";

const defaultValues = {
  age: 35,
  gender: "M",
  state: "MD",
  marital: "Married",
  profile: "salaried",
  has_card: true,
  has_marketing: true,
  engagement_segment: "active",
  has_personal_loan: 0 as 0 | 1,
  has_housing_loan: 0 as 0 | 1,
  has_credit_default: 0 as 0 | 1,
  bank_balance: 15000,
  was_previously_contacted: 0 as 0 | 1,
  prev_outcome_encoded: 0 as 0 | 1 | 2,
  education_ordinal: 3,
  loan_burden_score: 2,
};

function randomDepositValues(): typeof defaultValues {
  return {
    age: randInt(18, 90),
    gender: pick(["M", "F"] as const),
    state: pick(US_STATES),
    marital: pick(["Single", "Married", "Divorced", "Unknown"] as const),
    profile: pick(["salaried", "self_employed", "business", "other"] as const),
    has_card: Math.random() > 0.25,
    has_marketing: Math.random() > 0.4,
    engagement_segment: pick(["active", "moderate", "inactive", "dormant"] as const),
    has_personal_loan: pick([0, 1] as const),
    has_housing_loan: pick([0, 1] as const),
    has_credit_default: pick([0, 1] as const),
    bank_balance: randInt(0, 95000),
    was_previously_contacted: pick([0, 1] as const),
    prev_outcome_encoded: pick([0, 1, 2] as const),
    education_ordinal: randInt(1, 6),
    loan_burden_score: randInt(0, 10),
  };
}

export function DepositForm() {
  const [form, setForm] = useState(defaultValues);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScoreResponse | null>(null);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function onRandomize() {
    setForm(randomDepositValues());
    setResult(null);
    setError(null);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await scoreDeposit(form);
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Scoring failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="panel" onSubmit={onSubmit}>
      <h2>Deposit Propensity Prediction</h2>
      <p className="subtitle">Predict the likelihood a customer will open a deposit account.</p>

      <div className="grid grid-2">
        <section className="section">
          <h3>Customer Profile</h3>
          <Field label="Age">
            <input type="number" min={18} max={100} value={form.age} onChange={numberHandler((v) => update("age", v))} />
          </Field>
          <Field label="Gender">
            <select value={form.gender} onChange={stringHandler((v) => update("gender", v))}>
              <option value="M">M</option>
              <option value="F">F</option>
            </select>
          </Field>
          <Field label="State">
            <input value={form.state} onChange={stringHandler((v) => update("state", v))} />
          </Field>
          <Field label="Marital Status">
            <select value={form.marital} onChange={stringHandler((v) => update("marital", v))}>
              {["Single", "Married", "Divorced", "Unknown"].map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </Field>
          <Field label="Profile">
            <select value={form.profile} onChange={stringHandler((v) => update("profile", v))}>
              {["salaried", "self_employed", "business", "other"].map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </Field>
          <label className="checkbox-row">
            <input type="checkbox" checked={form.has_card} onChange={(e) => update("has_card", e.target.checked)} />
            Has Card
          </label>
          <label className="checkbox-row">
            <input type="checkbox" checked={form.has_marketing} onChange={(e) => update("has_marketing", e.target.checked)} />
            Has Marketing
          </label>
          <Field label="Engagement Segment">
            <select value={form.engagement_segment} onChange={stringHandler((v) => update("engagement_segment", v))}>
              {["active", "moderate", "inactive", "dormant"].map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </Field>
        </section>

        <section className="section">
          <h3>Financial & History</h3>
          <Field label="Has Personal Loan">
            <select
              value={form.has_personal_loan}
              onChange={stringHandler((v) => update("has_personal_loan", Number(v) as 0 | 1))}
            >
              <option value={0}>0</option>
              <option value={1}>1</option>
            </select>
          </Field>
          <Field label="Has Housing Loan">
            <select
              value={form.has_housing_loan}
              onChange={stringHandler((v) => update("has_housing_loan", Number(v) as 0 | 1))}
            >
              <option value={0}>0</option>
              <option value={1}>1</option>
            </select>
          </Field>
          <Field label="Has Credit Default">
            <select
              value={form.has_credit_default}
              onChange={stringHandler((v) => update("has_credit_default", Number(v) as 0 | 1))}
            >
              <option value={0}>0</option>
              <option value={1}>1</option>
            </select>
          </Field>
          <Field label="Bank Balance">
            <input type="number" min={0} max={100000} value={form.bank_balance} onChange={numberHandler((v) => update("bank_balance", v))} />
          </Field>
          <Field label="Was Previously Contacted">
            <select
              value={form.was_previously_contacted}
              onChange={stringHandler((v) => update("was_previously_contacted", Number(v) as 0 | 1))}
            >
              <option value={0}>0</option>
              <option value={1}>1</option>
            </select>
          </Field>
          <Field label="Previous Outcome">
            <select
              value={form.prev_outcome_encoded}
              onChange={stringHandler((v) => update("prev_outcome_encoded", Number(v) as 0 | 1 | 2))}
            >
              <option value={0}>Unknown</option>
              <option value={1}>Failure</option>
              <option value={2}>Success</option>
            </select>
          </Field>
          <Field label="Education Ordinal (1-6)">
            <input type="number" min={1} max={6} value={form.education_ordinal} onChange={numberHandler((v) => update("education_ordinal", v))} />
          </Field>
          <Field label="Loan Burden Score">
            <input type="number" min={0} max={10} value={form.loan_burden_score} onChange={numberHandler((v) => update("loan_burden_score", v))} />
          </Field>
        </section>
      </div>

      <div className="actions">
        <button className="primary-btn" type="button" onClick={onRandomize} disabled={loading}>
          Randomize metrics
        </button>
        <button className="primary-btn" type="submit" disabled={loading}>
          {loading ? "Scoring..." : "Predict Deposit Propensity"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {result && <ResultCard title="Deposit Propensity" result={result} />}
    </form>
  );
}
