export interface Zone {
  top: number;
  bottom: number;
  timeframe: string;
  impulse_strength: number;
  formed_at: string;
}

export interface Trade {
  entry: number;
  stop_loss: number;
  take_profit: number;
  rr_ratio: number;
  risk_pips: number;
  reward_pips: number;
}

export interface Breakdown {
  htf_alignment: number;
  impulse: number;
  rr: number;
  timeframe: number;
}

export interface Setup {
  pair: string;
  direction: "long" | "short";
  zone_type: "demand" | "supply";
  score: number;
  breakdown: Breakdown;
  zone: Zone;
  trade: Trade;
}

export interface Bias {
  d1_bias: string;
  h4_bias: string;
  overall_bias: string;
  aligned: boolean;
  trade_direction: string;
}

export interface ScanResult {
  status: string;
  refreshing?: boolean;
  setups: Setup[];
  pair_biases: Record<string, Bias>;
  scan_time?: string;
  pairs_scanned?: number;
  setups_found: number;
}