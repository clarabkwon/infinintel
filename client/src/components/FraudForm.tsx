import { FormEvent, useMemo, useState } from "react";
import { scoreFraud } from "../api";
import { randFloat, randInt } from "../randomize";
import type { ScoreResponse } from "../types";
import { Field, numberHandler } from "./FormControls";
import { ResultCard } from "./ResultCard";

const defaultValues = {
  amt: 150,
  amt_ratio: 1.2,
  amt_zscore: 0.5,
  cust_avg_amt: 125,
  cust_std_amt: 50,
  cust_velocity_1h: 2,
  cust_velocity_24h: 5,
  cust_velocity_7d: 15,
};

function randomFraudValues(): typeof defaultValues {
  const custAvg = randFloat(20, 800, 2);
  const custStd = randFloat(5, 400, 2);
  const amt = randFloat(5, 5000, 2);
  const ratio = custAvg > 0 ? Number((amt / custAvg).toFixed(2)) : 1;
  const z = custStd > 0 ? Number(((amt - custAvg) / custStd).toFixed(2)) : 0;
  return {
    amt,
    amt_ratio: Math.min(100, Math.max(0, ratio)),
    amt_zscore: Math.min(10, Math.max(-10, z)),
    cust_avg_amt: custAvg,
    cust_std_amt: custStd,
    cust_velocity_1h: randInt(0, 20),
    cust_velocity_24h: randInt(0, 80),
    cust_velocity_7d: randInt(0, 300),
  };
}

export function FraudForm() {
  const [form, setForm] = useState(defaultValues);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScoreResponse | null>(null);

  const logAmt = useMemo(() => Math.log1p(form.amt), [form.amt]);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function onRandomize() {
    setForm(randomFraudValues());
    setResult(null);
    setError(null);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await scoreFraud(form);
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
      <h2>Fraud Detection (Behavioral)</h2>
      <p className="subtitle">Detect potentially fraudulent transactions based on behavioral signals.</p>

      <div className="grid grid-2">
        <section className="section">
          <h3>Transaction</h3>
          <Field label="Transaction Amount ($)">
            <input type="number" min={0} max={50000} step={0.01} value={form.amt} onChange={numberHandler((v) => update("amt", v))} />
          </Field>
          <Field label="Log Amount (auto)">
            <input type="number" value={Number(logAmt.toFixed(4))} disabled readOnly />
          </Field>
          <Field label="Amount Ratio (vs avg)">
            <input type="number" min={0} max={100} step={0.01} value={form.amt_ratio} onChange={numberHandler((v) => update("amt_ratio", v))} />
          </Field>
          <Field label="Amount Z-Score">
            <input type="number" min={-10} max={10} step={0.01} value={form.amt_zscore} onChange={numberHandler((v) => update("amt_zscore", v))} />
          </Field>
        </section>

        <section className="section">
          <h3>Customer Behavior</h3>
          <Field label="Customer Avg Amount">
            <input type="number" min={0} max={50000} step={0.01} value={form.cust_avg_amt} onChange={numberHandler((v) => update("cust_avg_amt", v))} />
          </Field>
          <Field label="Customer Std Amount">
            <input type="number" min={0} max={10000} step={0.01} value={form.cust_std_amt} onChange={numberHandler((v) => update("cust_std_amt", v))} />
          </Field>
          <Field label="Velocity (1 hour)">
            <input type="number" min={0} max={100} value={form.cust_velocity_1h} onChange={numberHandler((v) => update("cust_velocity_1h", v))} />
          </Field>
          <Field label="Velocity (24 hours)">
            <input type="number" min={0} max={500} value={form.cust_velocity_24h} onChange={numberHandler((v) => update("cust_velocity_24h", v))} />
          </Field>
          <Field label="Velocity (7 days)">
            <input type="number" min={0} max={2000} value={form.cust_velocity_7d} onChange={numberHandler((v) => update("cust_velocity_7d", v))} />
          </Field>
        </section>
      </div>

      <div className="actions">
        <button className="primary-btn" type="button" onClick={onRandomize} disabled={loading}>
          Randomize metrics
        </button>
        <button className="primary-btn" type="submit" disabled={loading}>
          {loading ? "Scoring..." : "Detect Fraud"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {result && <ResultCard title="Fraud Probability" result={result} format="percent" />}
    </form>
  );
}
