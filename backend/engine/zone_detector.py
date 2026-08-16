import pandas as pd
from dataclasses import dataclass
from typing import Literal
import logging

logger = logging.getLogger(__name__)

ZoneType = Literal["supply", "demand"]


@dataclass
class Zone:
    type: ZoneType
    top: float
    bottom: float
    timeframe: str
    formed_index: int
    is_fresh: bool
    touch_count: int
    impulse_strength: float
    formed_at: str


def candle_body_size(candle: pd.Series) -> float:
    return abs(candle["close"] - candle["open"])


def is_base_candle(candle: pd.Series, avg_body: float) -> bool:
    body = candle_body_size(candle)
    return body < (avg_body * 0.5)


def impulse_strength(candles: pd.DataFrame) -> float:
    if candles.empty:
        return 0.0
    start_price = candles.iloc[0]["open"]
    end_price = candles.iloc[-1]["close"]
    if start_price == 0:
        return 0.0
    return abs((end_price - start_price) / start_price) * 100


def has_imbalance(candles: pd.DataFrame, direction: str) -> bool:
    if len(candles) < 3:
        return False
    first = candles.iloc[0]
    third = candles.iloc[2]

    if direction == "bullish":
        return third["low"] > first["high"]
    elif direction == "bearish":
        return third["high"] < first["low"]
    return False


def check_freshness(df: pd.DataFrame, zone: Zone) -> tuple[bool, int]:
    touch_count = 0
    after = df.iloc[zone.formed_index + 4:]

    for _, c in after.iterrows():
        if c["low"] <= zone.top and c["high"] >= zone.bottom:
            touch_count += 1

    return touch_count == 0, touch_count


def detect_zones(df: pd.DataFrame, timeframe: str, min_impulse: float = 0.1) -> list[Zone]:
    if df is None or len(df) < 10:
        return []

    zones = []
    avg_body = df.apply(candle_body_size, axis=1).mean()

    # Demand zones — Drop → Base → Rally
    for i in range(2, len(df) - 3):
        candle = df.iloc[i]

        if not is_base_candle(candle, avg_body):
            continue

        prior = df.iloc[i - 1]
        if prior["close"] >= prior["open"]:
            continue

        impulse = df.iloc[i + 1 : i + 4]
        strength = impulse_strength(impulse)

        if strength < min_impulse:
            continue

        if not has_imbalance(impulse, "bullish"):
            continue

        zone = Zone(
            type="demand",
            top=max(candle["open"], candle["close"]),
            bottom=min(candle["open"], candle["close"]),
            timeframe=timeframe,
            formed_index=i,
            is_fresh=True,
            touch_count=0,
            impulse_strength=round(strength, 4),
            formed_at=str(df.index[i]),
        )
        zone.is_fresh, zone.touch_count = check_freshness(df, zone)
        zones.append(zone)

    # Supply zones — Rally → Base → Drop
    for i in range(2, len(df) - 3):
        candle = df.iloc[i]

        if not is_base_candle(candle, avg_body):
            continue

        prior = df.iloc[i - 1]
        if prior["close"] <= prior["open"]:
            continue

        impulse = df.iloc[i + 1 : i + 4]
        strength = impulse_strength(impulse)

        if strength < min_impulse:
            continue

        if not has_imbalance(impulse, "bearish"):
            continue

        zone = Zone(
            type="supply",
            top=max(candle["open"], candle["close"]),
            bottom=min(candle["open"], candle["close"]),
            timeframe=timeframe,
            formed_index=i,
            is_fresh=True,
            touch_count=0,
            impulse_strength=round(strength, 4),
            formed_at=str(df.index[i]),
        )
        zone.is_fresh, zone.touch_count = check_freshness(df, zone)
        zones.append(zone)

    return zones


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    from data.fetcher import fetch_ohlcv

    df = fetch_ohlcv("GBPUSD=X", "H4")
    zones = detect_zones(df, "H4")

    fresh = [z for z in zones if z.is_fresh]
    print(f"Total zones: {len(zones)} | Fresh: {len(fresh)}")

    for z in fresh[:5]:
        print(f"{z.type.upper():7} {z.bottom:.5f} - {z.top:.5f} | "
              f"impulse {z.impulse_strength}% | touches {z.touch_count}")