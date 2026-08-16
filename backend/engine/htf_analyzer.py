import pandas as pd
from typing import Literal
import logging

logger = logging.getLogger(__name__)

Bias = Literal["bullish", "bearish", "neutral"]


def find_swing_points(df: pd.DataFrame, window: int = 3) -> tuple[list, list]:
    highs = []
    lows = []

    for i in range(window, len(df) - window):
        neighbourhood = df.iloc[i - window: i + window + 1]
        candle = df.iloc[i]

        if candle["high"] == neighbourhood["high"].max():
            highs.append(candle["high"])

        if candle["low"] == neighbourhood["low"].min():
            lows.append(candle["low"])

    return highs, lows


def determine_structure(df: pd.DataFrame) -> Bias:
    if df is None or len(df) < 20:
        return "neutral"

    highs, lows = find_swing_points(df)

    if len(highs) < 3 or len(lows) < 3:
        return "neutral"

    recent_highs = highs[-3:]
    recent_lows = lows[-3:]

    highs_rising = all(recent_highs[i] > recent_highs[i - 1] for i in range(1, 3))
    lows_rising = all(recent_lows[i] > recent_lows[i - 1] for i in range(1, 3))

    highs_falling = all(recent_highs[i] < recent_highs[i - 1] for i in range(1, 3))
    lows_falling = all(recent_lows[i] < recent_lows[i - 1] for i in range(1, 3))

    if highs_rising and lows_rising:
        return "bullish"
    if highs_falling and lows_falling:
        return "bearish"
    return "neutral"


def get_ema_bias(df: pd.DataFrame) -> Bias:
    if df is None or len(df) < 50:
        return "neutral"

    ema20 = df["close"].ewm(span=20, adjust=False).mean()
    ema50 = df["close"].ewm(span=50, adjust=False).mean()

    price = df["close"].iloc[-1]
    e20 = ema20.iloc[-1]
    e50 = ema50.iloc[-1]

    if price > e20 and price > e50 and e20 > e50:
        return "bullish"
    if price < e20 and price < e50 and e20 < e50:
        return "bearish"
    return "neutral"


def analyze_htf_bias(pair_data: dict) -> dict:
    d1 = pair_data.get("D1")
    h4 = pair_data.get("H4")

    d1_structure = determine_structure(d1)
    d1_ema = get_ema_bias(d1)
    h4_structure = determine_structure(h4)
    h4_ema = get_ema_bias(h4)

    def resolve(structure: Bias, ema: Bias) -> Bias:
        if structure != "neutral":
            return structure
        return ema

    d1_bias = resolve(d1_structure, d1_ema)
    h4_bias = resolve(h4_structure, h4_ema)

    if d1_bias != "neutral":
        overall = d1_bias
    elif h4_bias != "neutral":
        overall = h4_bias
    else:
        overall = "neutral"

    aligned = d1_bias == h4_bias and d1_bias != "neutral"

    if overall == "bullish":
        direction = "long"
    elif overall == "bearish":
        direction = "short"
    else:
        direction = "wait"

    return {
        "d1_bias": d1_bias,
        "h4_bias": h4_bias,
        "overall_bias": overall,
        "aligned": aligned,
        "trade_direction": direction,
    }


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    from data.fetcher import fetch_ohlcv

    data = {
        "D1": fetch_ohlcv("GBPUSD=X", "D1"),
        "H4": fetch_ohlcv("GBPUSD=X", "H4"),
    }

    bias = analyze_htf_bias(data)
    for k, v in bias.items():
        print(f"{k}: {v}")