"""Interpretable demand anomaly detection using robust Z scores."""
from __future__ import annotations

import numpy as np
import pandas as pd


def detect_anomalies(df: pd.DataFrame, limit: int = 8) -> list[dict]:
    sales = df.weekly_sales.astype(float)
    median = sales.median()
    mad = np.median(np.abs(sales - median))
    scale = 1.4826 * mad if mad else max(float(sales.std()), 1)
    z_scores = (sales - median) / scale
    results = []
    for index in np.where(np.abs(z_scores) >= 2.5)[0]:
        actual, z = sales.iloc[index], z_scores.iloc[index]
        deviation = (actual - median) / median * 100 if median else 0
        results.append({"date": df.date.iloc[index].strftime("%Y-%m-%d"), "actual_sales": int(actual), "expected_sales": round(median, 1), "z_score": round(float(z), 2), "pct_deviation": round(float(deviation), 1), "direction": "spike" if z > 0 else "drop", "severity": "high" if abs(z) >= 3.5 else "medium"})
    return sorted(results, key=lambda item: abs(item["z_score"]), reverse=True)[:limit]

