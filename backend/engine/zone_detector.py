import pandas as pd
from dataclasses import dataclass
from typing import Literal
import logging

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
    return body < (avg_body*0.5)

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

def detect_zones(df: pd.DataFrame, timeframe: str, min_impulse: float=0.1) ->list[Zone]:
    if df is None or len(df) < 10:
        return[]

    zones = []
    avg_body = df.apply(candle_body_size, axis=1).mean()

    for i in range(2, len(df) - 3):
        candle = df.iloc[i]

        if not is_base_candle(candle, avg_body):
            continue

        prior = df.iloc[i -1]
        if prior["close"] >= prior["open"]:
            continue

        impulse = df.iloc[i +1 : i + 4]
        strength = impulse_strength(impulse)

        if strength < min_impulse:
            continue

        if not has_imbalance(impulse, "bullish"):
            continue

        zone_top = max(candle["open"], candle["close"])
        zone_bottom = min(candle["open"], candle["close"])

        zones.append(Zone(
            type= "demand",
            top=zone_top,
            bottom= zone_bottom,
            timeframe=timeframe,
            formed_index= i,
            is_fresh= True,
            touch_count= 0,
            impulse_strength=round(strength, 4),
            formed_at=str(df.index[i]),
        ))
        return zones