import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { fetchCustomerOptions, lookupCustomer } from "../api";
import type { CustomerLookupResponse, CustomerOption } from "../types";

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function yesNo(value: boolean | null | undefined): string {
  if (value == null) return "N/A";
  return value ? "Yes" : "No";
}

function formatCustomerHeading(name: string, id: string): string {
  return `${name} (${id})`;
}

export function CustomerLookup() {
  const [query, setQuery] = useState("Mary Anderson (C000033)");
  const [options, setOptions] = useState<CustomerOption[]>([]);
  const [optionsError, setOptionsError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<CustomerLookupResponse | null>(null);
  const [resultTab, setResultTab] = useState<"churn" | "deposit" | "fraud">("churn");

  useEffect(() => {
    fetchCustomerOptions()
      .then((rows) => {
        setOptions(rows);
        setOptionsError(null);
      })
      .catch((err) => {
        setOptions([]);
        setOptionsError(err instanceof Error ? err.message : "Could not load customer list");
      });
  }, []);

  const filteredOptions = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return options.slice(0, 200);
    return options
      .filter(
        (opt) =>
          opt.customer_id.toLowerCase().includes(needle) ||
          opt.customer_name.toLowerCase().includes(needle) ||
          opt.label.toLowerCase().includes(needle),
      )
      .slice(0, 200);
  }, [options, query]);

  async function runLookup(value: string) {
    const raw = value.trim();
    if (!raw) {
      setError("Please enter or select a customer ID or name.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await lookupCustomer(raw);
      setData(result);
      setQuery(formatCustomerHeading(result.profile.customer_name, result.profile.customer_id));
      setResultTab("churn");
    } catch (err) {
      setData(null);
      setError(err instanceof Error ? err.message : "Lookup failed");
    } finally {
      setLoading(false);
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    await runLookup(query);
  }

  return (
    <section className="panel">
      <h2>Customer Lookup</h2>
      <p className="subtitle">
        Type a customer ID or name, or use the drop-down arrow in the box to pick from the list.
        Lookup loads churn, deposit propensity, fraud signals, and an AI stakeholder story based
        in that customer&apos;s data.
      </p>

      <form className="lookup-form" onSubmit={onSubmit}>
        <div className="field lookup-field">
          <label htmlFor="customer-query">Customer ID or name</label>
          <input
            id="customer-query"
            list="customer-options"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Mary Anderson or C000033"
            autoComplete="off"
          />
          <datalist id="customer-options">
            {filteredOptions.map((opt) => (
              <option key={opt.customer_id} value={opt.label} />
            ))}
          </datalist>
        </div>
        <button className="primary-btn" type="submit" disabled={loading}>
          {loading ? "Looking up…" : "Look Up Customer"}
        </button>
      </form>

      {optionsError && (
        <div className="error-banner">Customer list unavailable: {optionsError}</div>
      )}
      {error && <div className="error-banner">{error}</div>}

      {data && (
        <div className="lookup-results">
          <h3>
            Customer:{" "}
            {formatCustomerHeading(data.profile.customer_name, data.profile.customer_id)}
          </h3>

          {data.story && (
            <div className="customer-story">
              <div className="muted-label">Customer story</div>
              <p>{data.story}</p>
            </div>
          )}

          <div className="metric-grid">
            <div className="metric-tile">
              <span>Age</span>
              <strong>{data.profile.age ?? "N/A"}</strong>
            </div>
            <div className="metric-tile">
              <span>Gender</span>
              <strong>{data.profile.gender}</strong>
            </div>
            <div className="metric-tile">
              <span>State</span>
              <strong>{data.profile.state}</strong>
            </div>
            <div className="metric-tile">
              <span>Education</span>
              <strong>{data.profile.education}</strong>
            </div>
            <div className="metric-tile">
              <span>Marital</span>
              <strong>{data.profile.marital}</strong>
            </div>
            <div className="metric-tile">
              <span>Engagement</span>
              <strong>{data.profile.engagement_segment}</strong>
            </div>
          </div>

          <div className="tabs nested-tabs" aria-label="Lookup result tabs">
            {(
              [
                ["churn", "Churn Risk"],
                ["deposit", "Deposit Propensity"],
                ["fraud", "Fraud Detection"],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                className={`tab-btn${resultTab === id ? " active" : ""}`}
                onClick={() => setResultTab(id)}
              >
                {label}
              </button>
            ))}
          </div>

          {resultTab === "churn" &&
            (data.churn ? (
              <div className="result high">
                <div className="muted-label">Churn Probability</div>
                <div className="metric">{pct(data.churn.churn_probability)}</div>
                <div className="detail-grid">
                  <div className="metric-tile">
                    <span>Risk Band</span>
                    <strong>{data.churn.churn_risk_band}</strong>
                  </div>
                  <div className="metric-tile">
                    <span>Decision Threshold</span>
                    <strong>{pct(data.churn.decision_threshold)}</strong>
                  </div>
                </div>
              </div>
            ) : (
              <p className="empty-note">No churn score found for this customer.</p>
            ))}

          {resultTab === "deposit" &&
            (data.deposit ? (
              <div className="result info">
                <div className="muted-label">Deposit Propensity</div>
                <div className="metric">{pct(data.deposit.deposit_propensity)}</div>
                <div className="detail-grid">
                  <div className="metric-tile">
                    <span>Priority Band</span>
                    <strong>{data.deposit.priority_band}</strong>
                  </div>
                  <div className="metric-tile">
                    <span>Percentile</span>
                    <strong>{pct(data.deposit.propensity_percentile)}</strong>
                  </div>
                  <div className="metric-tile">
                    <span>Campaign Eligible</span>
                    <strong>{yesNo(data.deposit.campaign_eligible)}</strong>
                  </div>
                  <div className="metric-tile">
                    <span>Recommended</span>
                    <strong>{yesNo(data.deposit.recommended_for_campaign)}</strong>
                  </div>
                </div>
              </div>
            ) : (
              <p className="empty-note">No deposit propensity score found for this customer.</p>
            ))}

          {resultTab === "fraud" &&
            (data.fraud ? (
              <div className={`result ${data.fraud.risk_level}`}>
                <div className="muted-label">Fraud Probability</div>
                <div className="metric">{pct(data.fraud.fraud_score)}</div>
                <p className={`result-message ${data.fraud.risk_level}`}>{data.fraud.message}</p>
                <div className="detail-grid">
                  <div className="metric-tile">
                    <span>Amount</span>
                    <strong>
                      ${data.fraud.amt.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                    </strong>
                  </div>
                  <div className="metric-tile">
                    <span>Category</span>
                    <strong>{data.fraud.category}</strong>
                  </div>
                  <div className="metric-tile">
                    <span>Velocity (24h)</span>
                    <strong>{data.fraud.cust_velocity_24h}</strong>
                  </div>
                  <div className="metric-tile">
                    <span>Z-Score</span>
                    <strong>{data.fraud.amt_zscore.toFixed(2)}</strong>
                  </div>
                </div>
                <p className="caption">
                  Merchant: {data.fraud.merchant} | Date: {data.fraud.trans_date}
                </p>
              </div>
            ) : (
              <p className="empty-note">No transaction data found. Cannot score fraud model.</p>
            ))}
        </div>
      )}
    </section>
  );
}
