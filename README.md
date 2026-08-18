# ForecastIQ

> A full-stack supply-chain demand forecasting dashboard that turns weekly sales data into forecasts, inventory risk, and replenishment actions.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=111827)](https://react.dev/)

ForecastIQ is designed as a portfolio-grade planning tool rather than a notebook-only ML project. A planner selects a SKU and region, receives a four-week ensemble forecast with uncertainty, sees anomalous historical sales, and gets a stockout-risk recommendation grounded in supplier lead time and safety stock.

## Features

- Prophet + XGBoost ensemble forecasting with an 8-week holdout evaluation
- Forecast confidence bands and model MAE/MAPE reporting
- SKU and regional demand drill-down across 15 products and 4 regions
- Robust Z-score anomaly detection for unusually high or low demand periods
- Inventory risk classification: safe, warning, or critical
- Recommended replenishment quantity using lead-time demand plus reorder point
- Optional Groq-generated planner insight, with a no-key local fallback
- Deterministic synthetic retail dataset generator (6,240 weekly records)
- Responsive React dashboard and FastAPI-generated OpenAPI documentation

## Architecture

```text
React + Recharts dashboard
          │ HTTP
          ▼
FastAPI API ──► data loader ──► Prophet + XGBoost ensemble
     │                              │
     ├──► anomaly detector           └──► metrics + forecast interval
     └──► stockout engine ──► inventory recommendation + optional AI insight
```

## Repository layout

```text
forecastiq/
├── backend/                 # FastAPI service and forecasting logic
│   ├── main.py              # API routes and response composition
│   ├── forecaster.py        # Ensemble training, evaluation, prediction
│   ├── anomaly_detector.py  # Robust Z-score anomaly detection
│   ├── stockout_engine.py   # Risk and order-quantity calculation
│   └── tests/               # API smoke tests
├── data/generate_data.py    # Reproducible synthetic data generator
├── frontend/                # Vite + React dashboard
└── render.yaml              # Render backend deployment blueprint
```

## Run locally

### Prerequisites

- Python 3.10 or newer (Python 3.11 is recommended for Prophet compatibility)
- Node.js 18 or newer
- npm

### 1. Start the API

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
uvicorn backend.main:app --reload
```

The first API request automatically creates `backend/sales_data.csv`. Open [http://localhost:8000/docs](http://localhost:8000/docs) to explore the API.

> If PowerShell blocks virtual-environment activation, run `Set-ExecutionPolicy -Scope Process Bypass` once in that terminal, then activate it again.

### 2. Start the dashboard

In a second terminal from the repository root:

```powershell
Copy-Item frontend\.env.example frontend\.env
cd frontend
npm install
npm run dev
```

Open the local URL Vite prints (normally [http://localhost:5173](http://localhost:5173)). Choose a product and click **Run forecast**.

### Optional: enable Groq insights

Add your key to `backend/.env`:

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

Without this key, the app still works and produces a deterministic, plain-English local planning insight.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Service and dataset readiness check |
| `GET` | `/api/skus` | Available SKU catalog |
| `GET` | `/api/regions` | Region filters |
| `GET` | `/api/overview` | Category demand totals |
| `POST` | `/api/forecast` | Forecast, metrics, anomalies, risk, and insight |

Forecast request example:

```json
{
  "sku_id": "SKU_001",
  "region": "All",
  "periods": 4
}
```

## How the forecasting works

1. The most recent 8 weeks are held out for validation.
2. Prophet models annual seasonality and external demand drivers (holiday, promotion, temperature).
3. XGBoost models calendar variables, lagged demand (1/2/4/52 weeks), and rolling demand averages.
4. The final point forecast is the average of both models; uncertainty is based on Prophet’s interval around that ensemble point.
5. The final models are refit on all available history before generating the future horizon.

The stockout engine compares current stock with expected lead-time demand. It marks inventory as critical when stock is expected to deplete before replenishment arrives, and recommends enough units to cover lead-time demand plus the reorder point.

## Validation

With the virtual environment active:

```powershell
pytest backend/tests -q
```

The suite validates the health/catalog routes and verifies that a forecast returns the expected business outputs. For a production system, add time-series cross-validation, a model registry, data-quality checks, and monitoring for forecast drift.

## Deployment

### Backend (Render)

Push the repository to GitHub, create a Render Blueprint from `render.yaml`, and set `GROQ_API_KEY` only if you want AI-generated insights. The configured health check is `/health`.

### Frontend (Vercel)

Import the repository in Vercel with `frontend` as the root directory. Set:

```env
VITE_API_URL=https://your-render-service.onrender.com
```

## Future improvements

- Connect a real ERP/WMS inventory feed instead of synthetic data
- Add promotion and price scenario simulation
- Rank all SKUs by risk in a portfolio planning view
- Implement scheduled forecast refresh and Slack/email notifications
- Track model experiments and feature drift

## License

MIT — use this project freely for learning and portfolio purposes.
