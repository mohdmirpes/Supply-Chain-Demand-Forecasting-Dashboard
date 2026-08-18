"""Business insights with an optional Groq enhancement."""
from __future__ import annotations

import os


def local_insight(product: str, category: str, trend_pct: float, stockout: dict) -> str:
    trend = "above" if trend_pct >= 0 else "below"
    action = "increase safety stock and place the recommended replenishment order" if stockout["risk_level"] != "safe" else "maintain the current replenishment plan while monitoring weekly demand"
    return f"{product} demand is trending {abs(trend_pct):.1f}% {trend} its recent baseline. For this {category} SKU, {action}."


def generate_insight(product: str, category: str, trend_pct: float, stockout: dict) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return local_insight(product, category, trend_pct, stockout)
    try:
        from groq import Groq
        prompt = f"Write one concise supply-chain action insight for {product} ({category}). Trend: {trend_pct}%. Stockout risk: {stockout['risk_level']}; stock {stockout['current_stock']}; lead time {stockout['lead_time_weeks']} weeks. No greeting."
        response = Groq(api_key=key).chat.completions.create(model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"), messages=[{"role": "user", "content": prompt}], temperature=.2, max_tokens=90)
        return response.choices[0].message.content.strip()
    except Exception:
        return local_insight(product, category, trend_pct, stockout)

