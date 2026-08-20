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


def find_target_zone(zones: list[Zone], zone: Zone, current_price: float) -> float | None:
    opposing = "supply" if zone.type == "demand" else "demand"
    candidates = []

    for z in zones:
        if z.type != opposing:
            continue
        if zone.type == "demand" and z.bottom > current_price:
            candidates.append(z)
        elif zone.type == "supply" and z.top < current_price:
            candidates.append(z)

    if not candidates:
        return None

    if zone.type == "demand":
        return min(candidates, key=lambda z: z.bottom).bottom
    return max(candidates, key=lambda z: z.top).top


def calculate_rr(
    pair: str,
    zone: Zone,
    all_zones: list[Zone],
    current_price: float,
    sl_buffer_pips: int = 5,
    min_rr: float = 3.0,
) -> TradeSetup | None:
    pip = get_pip_size(pair)
    buffer = sl_buffer_pips * pip

    if zone.type == "demand":
        entry = zone.top
        stop_loss = zone.bottom - buffer
        risk = entry - stop_loss
        if risk <= 0:
            return None
        target = find_target_zone(all_zones, zone, current_price)
        take_profit = target if target else entry + (risk * min_rr)
        reward = take_profit - entry
        direction = "long"

    elif zone.type == "supply":
        entry = zone.bottom
        stop_loss = zone.top + buffer
        risk = stop_loss - entry
        if risk <= 0:
            return None
        target = find_target_zone(all_zones, zone, current_price)
        take_profit = target if target else entry - (risk * min_rr)
        reward = entry - take_profit
        direction = "short"

    else:
        return None

    if reward <= 0 or risk <= 0:
        return None

    rr_ratio = round(reward / risk, 2)

    if rr_ratio < min_rr:
        return None

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



