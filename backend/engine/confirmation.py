import pandas as pd
from engine.zone_detector import Zone
import logging

logger = logging.getLogger(__name__)


def distance_to_zone(zone: Zone, current_price: float) -> float:
    if zone.bottom <= current_price <= zone.top:
        return 0.0
    if current_price > zone.top:
        return ((current_price - zone.top) / current_price) * 100
    return ((zone.bottom - current_price) / current_price) * 100


def is_price_at_zone(zone: Zone, current_price: float, tolerance: float = 0.15) -> bool:
    return distance_to_zone(zone, current_price) <= tolerance


def find_recent_swing(df: pd.DataFrame, direction: str, window: int = 2) -> float | None:
    if df is None or len(df) < (window * 2 + 1):
        return None

    swings = []
    for i in range(window, len(df) - window):
        neighbourhood = df.iloc[i - window : i + window + 1]
        candle = df.iloc[i]

        if direction == "long":
            if candle["high"] == neighbourhood["high"].max():
                swings.append(candle["high"])
        else:
            if candle["low"] == neighbourhood["low"].min():
                swings.append(candle["low"])

    return swings[-1] if swings else None


def check_structure_shift(df: pd.DataFrame, direction: str, lookback: int = 30) -> bool:
    if df is None or len(df) < lookback:
        return False

    window = df.tail(lookback)
    split = len(window) // 2
    earlier = window.iloc[:split]
    later = window.iloc[split:]

    level = find_recent_swing(earlier, direction)
    if level is None:
        return False

    if direction == "long":
        return bool((later["close"] > level).any())
    return bool((later["close"] < level).any())


def evaluate_entry(zone: Zone, current_price: float, ltf_df: pd.DataFrame) -> dict:
    distance = round(distance_to_zone(zone, current_price), 3)

    if not is_price_at_zone(zone, current_price):
        return {"status": "approaching", "distance_pct": distance, "confirmed": False}

    direction = "long" if zone.type == "demand" else "short"
    shifted = check_structure_shift(ltf_df, direction)

    return {
        "status": "confirmed" if shifted else "at_zone",
        "distance_pct": distance,
        "confirmed": shifted,
    }