import datetime
import logging

from data.fetcher import fetch_all_pairs
from engine.zone_detector import detect_zones
from engine.htf_analyzer import analyze_htf_bias
from engine.rr_calculator import calculate_rr
from engine.scorer import score_setup, rank_setups, ScoredSetup

logger = logging.getLogger(__name__)


def run_scan() -> dict:
    scan_time = datetime.datetime.now(datetime.UTC).isoformat()
    all_data = fetch_all_pairs()

    all_setups: list[ScoredSetup] = []
    pair_biases = {}

    for pair, tf_data in all_data.items():
        if not tf_data:
            continue

        bias = analyze_htf_bias(tf_data)
        pair_biases[pair] = bias
        direction = bias["trade_direction"]

        if direction == "wait":
            continue

        h1 = tf_data.get("H1")
        if h1 is None or h1.empty:
            continue
        current_price = float(h1.iloc[-1]["close"])

        every_zone = []
        for tf in ["H4", "H1"]:
            df = tf_data.get(tf)
            if df is not None:
                every_zone.extend(detect_zones(df, tf))

        wanted = "demand" if direction == "long" else "supply"
        tradeable = []
        for z in every_zone:
            if z.type != wanted:
                continue
            if not z.is_fresh:
                continue
            if direction == "long" and z.top >= current_price:
                continue
            if direction == "short" and z.bottom <= current_price:
                continue
            tradeable.append(z)

        for zone in tradeable:
            setup = calculate_rr(pair, zone, every_zone, current_price, df=tf_data.get(zone.timeframe))
            if setup is None:
                continue
            all_setups.append(score_setup(setup, bias))

    ranked = rank_setups(all_setups)

    return {
        "setups": ranked,
        "pair_biases": pair_biases,
        "scan_time": scan_time,
        "pairs_scanned": len(all_data),
        "setups_found": len(ranked),
    }


def serialize(result: dict) -> dict:
    out = []
    for scored in result["setups"]:
        s = scored.setup
        out.append({
            "pair": s.pair,
            "direction": s.direction,
            "zone_type": s.zone_type,
            "score": scored.score,
            "breakdown": scored.breakdown,
            "zone": {
                "top": s.zone_top,
                "bottom": s.zone_bottom,
                "timeframe": s.timeframe,
                "impulse_strength": s.impulse_strength,
                "formed_at": s.formed_at,
            },
            "trade": {
                "entry": s.entry,
                "stop_loss": s.stop_loss,
                "take_profit": s.take_profit,
                "rr_ratio": s.rr_ratio,
                "risk_pips": s.risk_pips,
                "reward_pips": s.reward_pips,
            },
        })

    return {
        "setups": out,
        "pair_biases": result["pair_biases"],
        "scan_time": result["scan_time"],
        "pairs_scanned": result["pairs_scanned"],
        "setups_found": result["setups_found"],
    }


