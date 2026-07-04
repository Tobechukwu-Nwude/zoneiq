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

def impulse_strength(candles: pd.dataframes) -> float:
    if candles.empty:
        return 0.0
    start_price = candles.iloc[0]["open"]
    end_price = candles.iloc[-1]["close"]
    if start_price == 0:
        return 0.0
    return abs((end_price - start_price) / start_price) * 100

def has_imbalancee(candles: pd.DataFrame, direction: str) -> bool:
    if len(candles) < 3:
        return False
    first = candles.iloc[0]
    second = candles.iloc[2]

    if direction == "bullish":
        return third["low"] > first["hight"]
    elif direction == "bearish":
        return third["high"] < first["low"]
    return False