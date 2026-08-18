"""Forecasting service: Prophet + XGBoost ensemble with graceful fallback."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")

FEATURES = ["week", "month", "quarter", "year_idx", "is_holiday", "promotion", "temperature", "lag_1", "lag_2", "lag_4", "lag_52", "rolling_4", "rolling_12"]


def _features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["week"] = result.date.dt.isocalendar().week.astype(int)
    result["month"] = result.date.dt.month
    result["quarter"] = result.date.dt.quarter
    result["year_idx"] = result.date.dt.year - result.date.dt.year.min()
    for lag in (1, 2, 4, 52):
        result[f"lag_{lag}"] = result.weekly_sales.shift(lag)
    result["rolling_4"] = result.weekly_sales.shift(1).rolling(4).mean()
    result["rolling_12"] = result.weekly_sales.shift(1).rolling(12).mean()
    return result


def _fit_xgb(train: pd.DataFrame) -> XGBRegressor:
    frame = _features(train).dropna()
    model = XGBRegressor(n_estimators=160, learning_rate=.05, max_depth=3, subsample=.85, colsample_bytree=.85, random_state=42, n_jobs=1, verbosity=0)
    model.fit(frame[FEATURES], frame.weekly_sales)
    return model


def _xgb_predict(model: XGBRegressor, history: pd.DataFrame, periods: int) -> list[float]:
    work = history[["date", "weekly_sales", "is_holiday", "promotion", "temperature"]].copy()
    predictions: list[float] = []
    for _ in range(periods):
        next_date = work.date.max() + pd.Timedelta(weeks=1)
        sales = work.weekly_sales.to_numpy(dtype=float)
        payload = {"week": int(next_date.isocalendar().week), "month": next_date.month, "quarter": next_date.quarter, "year_idx": next_date.year - work.date.min().year, "is_holiday": 0, "promotion": float(work.promotion.tail(12).mean()), "temperature": float(work.temperature.tail(12).mean()), "lag_1": sales[-1], "lag_2": sales[-2], "lag_4": sales[-4], "lag_52": sales[-52] if len(sales) >= 52 else sales.mean(), "rolling_4": sales[-4:].mean(), "rolling_12": sales[-12:].mean()}
        value = max(0.0, float(model.predict(pd.DataFrame([payload])[FEATURES])[0]))
        predictions.append(value)
        work.loc[len(work)] = [next_date, value, 0, payload["promotion"], payload["temperature"]]
    return predictions


def _prophet_predict(train: pd.DataFrame, periods: int) -> tuple[list[float], list[float], list[float]]:
    try:
        from prophet import Prophet
        fit = train.rename(columns={"date": "ds", "weekly_sales": "y"})
        model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False, interval_width=.8)
        for col in ("is_holiday", "promotion", "temperature"):
            model.add_regressor(col)
        model.fit(fit[["ds", "y", "is_holiday", "promotion", "temperature"]])
        future = model.make_future_dataframe(periods=periods, freq="W-MON")
        future["is_holiday"] = 0
        future["promotion"] = float(train.promotion.tail(12).mean())
        future["temperature"] = float(train.temperature.tail(12).mean())
        prediction = model.predict(future).tail(periods)
        return prediction.yhat.clip(lower=0).tolist(), prediction.yhat_lower.clip(lower=0).tolist(), prediction.yhat_upper.clip(lower=0).tolist()
    except Exception:
        values = train.weekly_sales.to_numpy(dtype=float)
        base = [float(values[-52 + index]) if len(values) >= 52 else float(values[-12:].mean()) for index in range(periods)]
        spread = max(float(np.std(values[-12:])), 1.0) * 1.28
        return base, [max(0, x - spread) for x in base], [x + spread for x in base]


def _mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    valid = actual != 0
    return float(np.mean(np.abs((actual[valid] - predicted[valid]) / actual[valid])) * 100) if valid.any() else 0.0


def forecast(data: pd.DataFrame, periods: int = 4) -> dict:
    """Evaluate on the last eight weeks, then refit and predict requested weeks."""
    if len(data) < 70:
        raise ValueError("At least 70 weeks of history are required.")
    data = data.sort_values("date").reset_index(drop=True)
    holdout, train = min(8, max(4, len(data) // 5)), data.iloc[:-8].copy()
    actual = data.iloc[-holdout:].weekly_sales.to_numpy(dtype=float)
    xgb = _fit_xgb(train)
    xgb_eval = np.array(_xgb_predict(xgb, train, holdout))
    prophet_eval, _, _ = _prophet_predict(train, holdout)
    prophet_eval = np.array(prophet_eval)
    ensemble_eval = (xgb_eval + prophet_eval) / 2
    final_xgb = _fit_xgb(data)
    xgb_values = np.array(_xgb_predict(final_xgb, data, periods))
    prophet_values, lower, upper = _prophet_predict(data, periods)
    point = (xgb_values + np.array(prophet_values)) / 2
    dates = pd.date_range(data.date.max() + pd.Timedelta(weeks=1), periods=periods, freq="W-MON")
    interval_radius = np.maximum(point - np.array(lower), np.array(upper) - point)
    predictions = [{"date": date.strftime("%Y-%m-%d"), "forecast": round(float(value), 1), "lower": round(float(max(0, value - radius)), 1), "upper": round(float(value + radius), 1)} for date, value, radius in zip(dates, point, interval_radius)]
    recent, prior = data.weekly_sales.tail(4).mean(), data.weekly_sales.iloc[-8:-4].mean()
    trend = ((recent - prior) / prior * 100) if prior else 0
    return {"forecast": predictions, "trend_pct": round(float(trend), 1), "metrics": {"prophet": {"mae": round(float(mean_absolute_error(actual, prophet_eval)), 1), "mape": round(_mape(actual, prophet_eval), 1)}, "xgboost": {"mae": round(float(mean_absolute_error(actual, xgb_eval)), 1), "mape": round(_mape(actual, xgb_eval), 1)}, "ensemble": {"mae": round(float(mean_absolute_error(actual, ensemble_eval)), 1), "mape": round(_mape(actual, ensemble_eval), 1)}}}

