"""FastAPI application for ForecastIQ."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .anomaly_detector import detect_anomalies
from .data_loader import get_sku_data, get_sku_list, load_data
from .forecaster import forecast
from .insights import generate_insight
from .models import ForecastRequest, HealthResponse
from .stockout_engine import assess_stockout

app = FastAPI(title="ForecastIQ API", version="1.0.0", description="Demand forecasts and inventory recommendations.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "records": len(load_data())}


@app.get("/api/skus")
def skus():
    return {"skus": get_sku_list(load_data())}


@app.get("/api/regions")
def regions():
    return {"regions": ["All", "North", "South", "East", "West"]}


@app.get("/api/overview")
def overview():
    df = load_data()
    categories = df.groupby("category", as_index=False).weekly_sales.sum().rename(columns={"weekly_sales": "total_sales"})
    return {"categories": categories.to_dict("records")}


@app.post("/api/forecast")
def run_forecast(request: ForecastRequest):
    try:
        data = get_sku_data(load_data(), request.sku_id, request.region)
        result = forecast(data, request.periods)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    latest = data.iloc[-1].to_dict()
    stockout = assess_stockout(latest, result["forecast"])
    result.update({"sku_id": request.sku_id, "region": request.region, "product_name": latest["product_name"], "category": latest["category"], "historical": [{"date": row.date.strftime("%Y-%m-%d"), "weekly_sales": int(row.weekly_sales)} for row in data.itertuples()], "anomalies": detect_anomalies(data), "stockout": stockout, "insight": generate_insight(latest["product_name"], latest["category"], result["trend_pct"], stockout)})
    return result
