

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
