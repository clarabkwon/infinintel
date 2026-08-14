import { FormEvent, useState } from "react";
import { scoreChurn } from "../api";
import { pick, randFloat, randInt, US_STATES } from "../randomize";
import type { ScoreResponse } from "../types";
import { Field, numberHandler, stringHandler } from "./FormControls";
import { ResultCard } from "./ResultCard";

const defaultValues = {
  age: 45,
  gender: "M",
  state: "VA",
  education: "Graduate",
  marital: "Married",
  profile: "salaried",
  has_card: true,
  has_marketing: false,
  engagement_segment: "active",
  card_category: "Blue",
  income_category: "$60K - $80K",
  months_on_book: 36,
  months_inactive_12m: 2,
  contacts_count_12m: 3,
  credit_limit: 8000,
  revolving_balance: 1500,
  utilization_ratio: 0.3,
  acct_dependent_count: 2,
  acct_total_relationship_count: 4,
  acct_total_trans_amt: 5000,
  acct_total_trans_ct: 60,
  acct_total_amt_chng_q4_q1: 0.8,
  acct_total_ct_chng_q4_q1: 0.7,
};

function randomChurnValues(): typeof defaultValues {
  return {
    age: randInt(18, 90),
    gender: pick(["M", "F"] as const),
    state: pick(US_STATES),
    education: pick([
      "Uneducated",
      "High School",
      "College",
      "Graduate",
      "Post-Graduate",
      "Doctorate",
    ] as const),
    marital: pick(["Single", "Married", "Divorced", "Unknown"] as const),
    profile: pick(["salaried", "self_employed", "business", "other"] as const),
    has_card: Math.random() > 0.2,
    has_marketing: Math.random() > 0.5,
    engagement_segment: pick(["active", "moderate", "inactive", "dormant"] as const),
    card_category: pick(["Blue", "Silver", "Gold", "Platinum"] as const),
    income_category: pick([
      "Less than $40K",
      "$40K - $60K",
      "$60K - $80K",
      "$80K - $120K",
      "$120K +",
    ] as const),
    months_on_book: randInt(1, 60),
    months_inactive_12m: randInt(0, 12),
    contacts_count_12m: randInt(0, 12),
    credit_limit: randInt(500, 40000),
    revolving_balance: randInt(0, 25000),
    utilization_ratio: randFloat(0, 1, 2),
    acct_dependent_count: randInt(0, 8),
    acct_total_relationship_count: randInt(1, 10),
    acct_total_trans_amt: randInt(100, 45000),
    acct_total_trans_ct: randInt(1, 180),
    acct_total_amt_chng_q4_q1: randFloat(0, 3, 2),
    acct_total_ct_chng_q4_q1: randFloat(0, 3, 2),
  };
}

export function ChurnForm() {
  const [form, setForm] = useState(defaultValues);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScoreResponse | null>(null);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function onRandomize() {
    setForm(randomChurnValues());
    setResult(null);
    setError(null);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await scoreChurn(form);
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
      <h2>Customer Churn Prediction</h2>
      <p className="subtitle">
        Predict whether a customer is likely to churn based on demographics and account activity.
      </p>

      <div className="grid grid-3">
        <section className="section">
          <h3>Demographics</h3>
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
          <Field label="Education">
            <select value={form.education} onChange={stringHandler((v) => update("education", v))}>
              {["Uneducated", "High School", "College", "Graduate", "Post-Graduate", "Doctorate"].map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
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
        </section>

        <section className="section">
          <h3>Account Info</h3>
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
          <Field label="Card Category">
            <select value={form.card_category} onChange={stringHandler((v) => update("card_category", v))}>
              {["Blue", "Silver", "Gold", "Platinum"].map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </Field>
          <Field label="Income Category">
            <select value={form.income_category} onChange={stringHandler((v) => update("income_category", v))}>
              {["Less than $40K", "$40K - $60K", "$60K - $80K", "$80K - $120K", "$120K +"].map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </Field>
          <Field label="Months on Book">
            <input type="number" min={1} max={60} value={form.months_on_book} onChange={numberHandler((v) => update("months_on_book", v))} />
          </Field>
          <Field label="Months Inactive (12m)">
            <input type="number" min={0} max={12} value={form.months_inactive_12m} onChange={numberHandler((v) => update("months_inactive_12m", v))} />
          </Field>
          <Field label="Contacts Count (12m)">
            <input type="number" min={0} max={12} value={form.contacts_count_12m} onChange={numberHandler((v) => update("contacts_count_12m", v))} />
          </Field>
        </section>

        <section className="section">
          <h3>Financial Metrics</h3>
          <Field label="Credit Limit">
            <input type="number" min={0} max={50000} value={form.credit_limit} onChange={numberHandler((v) => update("credit_limit", v))} />
          </Field>
          <Field label="Revolving Balance">
            <input type="number" min={0} max={30000} value={form.revolving_balance} onChange={numberHandler((v) => update("revolving_balance", v))} />
          </Field>
          <Field label="Utilization Ratio">
            <input type="number" min={0} max={1} step={0.01} value={form.utilization_ratio} onChange={numberHandler((v) => update("utilization_ratio", v))} />
          </Field>
          <Field label="Dependent Count">
            <input type="number" min={0} max={10} value={form.acct_dependent_count} onChange={numberHandler((v) => update("acct_dependent_count", v))} />
          </Field>
          <Field label="Total Relationship Count">
            <input type="number" min={1} max={10} value={form.acct_total_relationship_count} onChange={numberHandler((v) => update("acct_total_relationship_count", v))} />
          </Field>
          <Field label="Total Transaction Amount">
            <input type="number" min={0} max={50000} value={form.acct_total_trans_amt} onChange={numberHandler((v) => update("acct_total_trans_amt", v))} />
          </Field>
          <Field label="Total Transaction Count">
            <input type="number" min={0} max={200} value={form.acct_total_trans_ct} onChange={numberHandler((v) => update("acct_total_trans_ct", v))} />
          </Field>
          <Field label="Amt Change Q4/Q1">
            <input type="number" min={0} max={3} step={0.01} value={form.acct_total_amt_chng_q4_q1} onChange={numberHandler((v) => update("acct_total_amt_chng_q4_q1", v))} />
          </Field>
          <Field label="Ct Change Q4/Q1">
            <input type="number" min={0} max={3} step={0.01} value={form.acct_total_ct_chng_q4_q1} onChange={numberHandler((v) => update("acct_total_ct_chng_q4_q1", v))} />
          </Field>
        </section>
      </div>

      <div className="actions">
        <button className="primary-btn" type="button" onClick={onRandomize} disabled={loading}>
          Randomize metrics
        </button>
        <button className="primary-btn" type="submit" disabled={loading}>
          {loading ? "Scoring..." : "Predict Churn"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {result && <ResultCard title="Churn Probability" result={result} />}
    </form>
  );
}
