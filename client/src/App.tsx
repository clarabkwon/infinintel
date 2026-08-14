import { useEffect, useState } from "react";
import { fetchConfig } from "./api";
import { ChurnForm } from "./components/ChurnForm";
import { CustomerLookup } from "./components/CustomerLookup";
import { DepositForm } from "./components/DepositForm";
import { FraudForm } from "./components/FraudForm";
import type { AppConfig, TabId } from "./types";

const tabs: { id: TabId; label: string }[] = [
  { id: "lookup", label: "Customer Lookup" },
  { id: "churn", label: "Churn Prediction" },
  { id: "deposit", label: "Deposit Propensity" },
  { id: "fraud", label: "Fraud Detection" },
];

export default function App() {
  const [tab, setTab] = useState<TabId>("lookup");
  const [config, setConfig] = useState<AppConfig | null>(null);

  useEffect(() => {
    fetchConfig()
      .then(setConfig)
      .catch(() => {
        setConfig({
          auth: "oauth_app_service_principal",
          endpoints: {
            churn: "churn-xgboost",
            deposit: "deposit-propensity-xgboost",
            fraud: "fraud-xgb-behavioral",
          },
        });
      });
  }, []);

  return (
    <div className="app-shell">
      <header className="hero">
        <h1 className="app-title">InfinIntel</h1>
        <p className="app-description">
          Look up a customer for precomputed risk scores based on customer ID, or manually score
          churn, deposit propensity, and fraud with Databricks Model Serving.
        </p>
      </header>

      <nav className="tabs" aria-label="Model tabs">
        {tabs.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`tab-btn${tab === item.id ? " active" : ""}`}
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <main className="app-main">
        {tab === "lookup" && <CustomerLookup />}
        {tab === "churn" && <ChurnForm />}
        {tab === "deposit" && <DepositForm />}
        {tab === "fraud" && <FraudForm />}
      </main>

      <footer className="footer">InfinIntel | 2026</footer>
    </div>
  );
}
