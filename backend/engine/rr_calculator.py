import pandas as pd
from dataclasses import dataclass
from engine.zone_detector import Zone
import logging

logger = logging.getLogger(__name__)

PIP_SIZES = {
    "EURUSD": 0.0001,
    "GBPUSD": 0.0001,
    "AUDUSD": 0.0001,
    "USDCAD": 0.0001,
    "EURCAD": 0.0001,
    "USDJPY": 0.01,
    "GBPJPY": 0.01,
    "XAUUSD": 0.1,
}


@dataclass
class TradeSetup:
    pair: str
    direction: str
    zone_type: str
    zone_top: float
    zone_bottom: float
    entry: float
    stop_loss: float
    take_profit: float
    rr_ratio: float
    risk_pips: float
    reward_pips: float
    timeframe: str
    impulse_strength: float
    formed_at: str


def get_pip_size(pair: str) -> float:
    return PIP_SIZES.get(pair, 0.0001)


def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    if df is None or len(df) < period + 1:
        return 0.0

    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return float(true_range.tail(period).mean())


def find_target_zone(zones: list[Zone], zone: Zone, entry: float) -> float | None:
    opposing = "supply" if zone.type == "demand" else "demand"
    candidates = []

    for z in zones:
        if z.type != opposing:
            continue
        if zone.type == "demand" and z.bottom > entry:
            candidates.append(z.bottom)
        elif zone.type == "supply" and z.top < entry:
            candidates.append(z.top)

    if not candidates:
        return None

    if zone.type == "demand":
        return min(candidates)
    return max(candidates)


def calculate_rr(
    pair: str,
    zone: Zone,
    all_zones: list[Zone],
    current_price: float,
    df: pd.DataFrame = None,
    min_rr: float = 3.0,
    max_rr: float = 10.0,
) -> TradeSetup | None:
    pip = get_pip_size(pair)

    atr = calculate_atr(df) if df is not None else 0.0
    buffer = atr * 0.5 if atr > 0 else 10 * pip

    if zone.type == "demand":
        entry = zone.top
        stop_loss = zone.bottom - buffer
        risk = entry - stop_loss
        direction = "long"
    elif zone.type == "supply":
        entry = zone.bottom
        stop_loss = zone.top + buffer
        risk = stop_loss - entry
        direction = "short"
    else:
        return None

    if risk <= 0:
        return None

    target = find_target_zone(all_zones, zone, entry)

    if target is None:
        take_profit = entry + (risk * min_rr) if direction == "long" else entry - (risk * min_rr)
    else:
        take_profit = target

    reward = take_profit - entry if direction == "long" else entry - take_profit

    if reward <= 0:
        return None

    rr_ratio = round(reward / risk, 2)

    if rr_ratio < min_rr:
        return None

    if rr_ratio > max_rr:
        capped = risk * max_rr
        take_profit = entry + capped if direction == "long" else entry - capped
        reward = capped
        rr_ratio = max_rr

    return TradeSetup(
        pair=pair,
        direction=direction,
        zone_type=zone.type,
        zone_top=round(zone.top, 5),
        zone_bottom=round(zone.bottom, 5),
        entry=round(entry, 5),
        stop_loss=round(stop_loss, 5),
        take_profit=round(take_profit, 5),
        rr_ratio=rr_ratio,
        risk_pips=round(risk / pip, 1),
        reward_pips=round(reward / pip, 1),
        timeframe=zone.timeframe,
        impulse_strength=zone.impulse_strength,
        formed_at=zone.formed_at,
    )