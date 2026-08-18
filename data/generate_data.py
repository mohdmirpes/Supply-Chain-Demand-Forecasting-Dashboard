"""Generate a deterministic, realistic weekly retail demand dataset."""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

RNG_SEED = 42
CATEGORIES = {
    "Electronics": {"base": 120, "seasonality": "winter_high", "price": (800, 5000)},
    "Clothing": {"base": 200, "seasonality": "spring_fall", "price": (300, 2000)},
    "Food": {"base": 500, "seasonality": "steady", "price": (50, 500)},
    "Furniture": {"base": 40, "seasonality": "spring_high", "price": (2000, 15000)},
    "Personal Care": {"base": 300, "seasonality": "steady", "price": (100, 800)},
}
PRODUCTS = [
    ("SKU_001", "Apex Wireless Headphones", "Electronics"), ("SKU_002", "Nova Laptop Pro 15", "Electronics"),
    ("SKU_003", "Zenith Smartphone X12", "Electronics"), ("SKU_004", "Core Running Shoes", "Clothing"),
    ("SKU_005", "Peak Winter Jacket", "Clothing"), ("SKU_006", "Orbit Sports T-Shirt", "Clothing"),
    ("SKU_007", "Crest Protein Snack Bar", "Food"), ("SKU_008", "Valo Instant Coffee 500g", "Food"),
    ("SKU_009", "Nova Mineral Water 24-pack", "Food"), ("SKU_010", "Apex Office Chair Ergonomic", "Furniture"),
    ("SKU_011", "Zenith Study Desk 120cm", "Furniture"), ("SKU_012", "Core Anti-Aging Serum", "Personal Care"),
    ("SKU_013", "Orbit Daily Sunscreen SPF50", "Personal Care"), ("SKU_014", "Peak Bluetooth Speaker Mini", "Electronics"),
    ("SKU_015", "Valo Dining Table 6-Seater", "Furniture"),
]
REGIONS = ["North", "South", "East", "West"]
HOLIDAYS = {"2023-01-26", "2023-03-08", "2023-08-15", "2023-10-02", "2023-10-24", "2023-12-25", "2024-01-26", "2024-03-25", "2024-08-15", "2024-10-02", "2024-10-31", "2024-12-25"}


def seasonal_factor(date: datetime, pattern: str) -> float:
    patterns = {
        "winter_high": [1.3, 1.0, .9, .85, .8, .75, .8, .9, 1.0, 1.2, 1.4, 1.5],
        "spring_fall": [.9, .95, 1.2, 1.3, 1.1, .85, .8, .9, 1.2, 1.3, 1.1, 1.0],
        "spring_high": [.7, .8, 1.3, 1.4, 1.2, .9, .8, .85, 1.0, 1.1, .9, .8],
        "steady": [1.0] * 12,
    }
    return patterns[pattern][date.month - 1]


def generate(output_path: Path | None = None) -> pd.DataFrame:
    """Create 15 SKUs × 4 regions × 104 weekly observations."""
    np.random.seed(RNG_SEED)
    random.seed(RNG_SEED)
    rows: list[dict] = []
    start = datetime(2023, 1, 2)
    for sku_id, product_name, category in PRODUCTS:
        info = CATEGORIES[category]
        base = info["base"]
        price = round(random.uniform(*info["price"]), 2)
        slope = random.uniform(.001, .005)
        for region in REGIONS:
            multiplier = {"North": 1.1, "South": .9, "East": 1.0, "West": 1.05}[region]
            stock = int(base * 8)
            for week in range(104):
                date = start + timedelta(weeks=week)
                date_str = date.strftime("%Y-%m-%d")
                holiday = int(date_str in HOLIDAYS)
                promotion = int(random.random() < .15)
                temperature = round(20 + 10 * np.sin(2 * np.pi * (date.month - 3) / 12) + random.uniform(-3, 3), 1)
                temperature_factor = 1.1 if category in {"Electronics", "Furniture"} and temperature < 20 else (.95 if category in {"Electronics", "Furniture"} else 1)
                expected = base * seasonal_factor(date, info["seasonality"]) * (1 + slope * week) * multiplier * (1.25 if holiday else 1) * (1.3 if promotion else 1) * temperature_factor
                sales = max(0, int(expected + np.random.normal(0, expected * .1)))
                reorder_point = int(base * 1.5)
                lead_time = random.choice([1, 2, 2, 3])
                stock = max(0, stock - sales)
                rows.append({"date": date_str, "sku_id": sku_id, "product_name": product_name, "category": category, "region": region, "weekly_sales": sales, "unit_price": price, "is_holiday": holiday, "promotion": promotion, "temperature": temperature, "current_stock": stock, "reorder_point": reorder_point, "lead_time_weeks": lead_time})
                if stock < reorder_point:
                    stock += int(base * 6)
    dataframe = pd.DataFrame(rows)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_csv(output_path, index=False)
    return dataframe


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "backend" / "sales_data.csv"
    frame = generate(target)
    print(f"Generated {len(frame):,} rows at {target}")
