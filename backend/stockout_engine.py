"""Translate forecast values into inventory action recommendations."""
from __future__ import annotations

import math


def assess_stockout(latest: dict, forecast: list[dict]) -> dict:
    weekly = [point["forecast"] for point in forecast]
    demand_4w = sum(weekly)
    avg_demand = demand_4w / max(len(weekly), 1)
    stock = max(0, int(latest["current_stock"]))
    reorder_point = int(latest["reorder_point"])
    lead = max(1, int(round(latest["lead_time_weeks"])))
    weeks_until = round(stock / avg_demand, 1) if avg_demand else float("inf")
    lead_demand = avg_demand * lead
    if weeks_until < lead:
        risk, message = "critical", "Inventory is expected to run out before a new order can arrive. Order now."
    elif stock <= reorder_point or weeks_until < lead + 1:
        risk, message = "warning", "Inventory is approaching its reorder threshold. Plan replenishment this week."
    else:
        risk, message = "safe", "Inventory should cover expected demand through the supplier lead time."
    recommended = max(0, math.ceil(lead_demand + reorder_point - stock))
    return {"risk_level": risk, "risk_message": message, "current_stock": stock, "reorder_point": reorder_point, "lead_time_weeks": lead, "weeks_until_stockout": weeks_until, "total_forecast_4w": round(demand_4w, 1), "recommended_order_qty": recommended}

