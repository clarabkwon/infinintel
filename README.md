# InfinIntel

Full-stack Databricks App with **customer lookup** (Unity Catalog + SQL warehouse) plus live scoring for **churn**, **deposit propensity**, and **fraud** via Model Serving.

# Demo


https://github.com/user-attachments/assets/86e09ebd-6821-43d5-9e0e-9362b563fc3a


## Stack

- **Frontend:** React + TypeScript + Vite
- **Backend:** FastAPI + Pydantic
- **Auth:** Databricks Apps OAuth — SQL via user token (OBO), scoring via app service principal

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

npm install

# Terminal 1 — API
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — UI (proxies /api → :8000)
npm run dev
```

Open http://localhost:5173

Configure Databricks auth locally (`DATABRICKS_HOST` + token/profile, or Databricks CLI).

## Tests

```bash
pip install pytest
PYTHONPATH=. pytest tests/ -v
```

Feature-builder tests do not require Databricks credentials. Live scoring against Model Serving does.

## Databricks Apps

- Root `package.json` triggers `npm install` + `npm run build` on deploy.
- `app.yaml` starts `uvicorn app:app --host 0.0.0.0 --port 8000`.
- FastAPI serves the built SPA from `client/dist` and exposes `/api/score/*`.

## API

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/lookup/{customer_id}` | Profile + churn/deposit tables + live fraud score |
| POST | `/api/score/churn` | `churn-xgboost` |
| POST | `/api/score/deposit` | `deposit-propensity-xgboost` |
| POST | `/api/score/fraud` | `fraud-xgb-behavioral` |
| GET | `/api/health` | — |
| GET | `/api/config` | — |

Lookup reads `internship2026.team2.customer_dimension_silver`, `churn_predictions_v1`, `deposit_propensity_predictions_v1`, and `fraud_features_table`.
