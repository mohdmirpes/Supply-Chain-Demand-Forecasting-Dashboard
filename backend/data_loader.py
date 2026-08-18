"""Dataset access and SKU-level aggregation helpers."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).with_name("sales_data.csv")


@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        from data.generate_data import generate
        generate(DATA_PATH)
    return pd.read_csv(DATA_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)


def get_sku_list(df: pd.DataFrame) -> list[dict]:
    return df[["sku_id", "product_name", "category"]].drop_duplicates().sort_values("sku_id").to_dict("records")


def get_sku_data(df: pd.DataFrame, sku_id: str, region: str = "All") -> pd.DataFrame:
    sku = df[df.sku_id == sku_id]
    if sku.empty:
        raise ValueError(f"Unknown SKU: {sku_id}")
    if region != "All":
        region_data = sku[sku.region == region].copy()
        if region_data.empty:
            raise ValueError(f"Unknown region: {region}")
        return region_data
    return sku.groupby("date", as_index=False).agg({
        "weekly_sales": "sum", "is_holiday": "max", "promotion": "max", "temperature": "mean",
        "current_stock": "sum", "reorder_point": "sum", "lead_time_weeks": "mean", "unit_price": "first",
        "product_name": "first", "category": "first",
    })

