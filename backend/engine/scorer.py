from dataclasses import dataclass
from engine.rr_calculator import TradeSetup


@dataclass
class ScoredSetup:
    setup: TradeSetup
    score: float
    breakdown: dict


def score_setup(setup: TradeSetup, htf_bias: dict) -> ScoredSetup:
    score = 0.0
    breakdown = {}

    aligned = htf_bias.get("aligned", False)
    overall = htf_bias.get("overall_bias", "neutral")

    expected = "demand" if overall == "bullish" else "supply" if overall == "bearish" else None
    bias_match = expected == setup.zone_type

    if aligned and bias_match:
        score += 3.0
        breakdown["htf_alignment"] = 3.0
    elif bias_match:
        score += 1.5
        breakdown["htf_alignment"] = 1.5
    else:
        breakdown["htf_alignment"] = 0.0

    if setup.impulse_strength >= 0.5:
        score += 3.0
        breakdown["impulse"] = 3.0
    elif setup.impulse_strength >= 0.3:
        score += 2.0
        breakdown["impulse"] = 2.0
    elif setup.impulse_strength >= 0.1:
        score += 1.0
        breakdown["impulse"] = 1.0
    else:
        breakdown["impulse"] = 0.0

    if setup.rr_ratio >= 5.0:
        score += 3.0
        breakdown["rr"] = 3.0
    elif setup.rr_ratio >= 4.0:
        score += 2.0
        breakdown["rr"] = 2.0
    elif setup.rr_ratio >= 3.0:
        score += 1.0
        breakdown["rr"] = 1.0
    else:
        breakdown["rr"] = 0.0

    if setup.timeframe == "H4":
        score += 1.0
        breakdown["timeframe"] = 1.0
    else:
        breakdown["timeframe"] = 0.0

    return ScoredSetup(setup=setup, score=min(round(score, 1), 10.0), breakdown=breakdown)


def rank_setups(setups: list[ScoredSetup], min_score: float = 4.0) -> list[ScoredSetup]:
    valid = [s for s in setups if s.score >= min_score]
    return sorted(valid, key=lambda s: s.score, reverse=True)