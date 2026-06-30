import yfinance as yf
import pandas as pd
import logging

logger = logging.getLogger(__name__)

PAIRS = ["EURUSD=X",
         "GBPUSD=X",
         "XAUUSD=X",
         "AUDUSD=X",
         "USDCAD=X",
         "EURCAD=X",
         "USDJPY=X",
         "GBPJPY=X"
         ]
TIMEFRAMES = {"D1": {"interval":"1d", "period": "180d"},
              "H4": {"interval":"1h", "period": "60d"},
              "H1": {"interval":"1h", "period": "30d"}}

PAIR_LABELS = {"EURUSD=X":"EURUSD",
               "GBPUSD=X":"GBPUSD",
               "USDJPY=X":"USDJPY",
               "GBPJPY=X":"GBPJPY",
               "XAUUSD=X":"XAUUSD",
               "AUDUSD=X":"AUDUSD",
               "USDCAD=X":"USDCAD",
               "EURCAD=X":"EURCAD",
               }

def fetch_ohlcv(symbol: str, timeframe: str) -> pd.DataFrame | None:
    try:
        config = TIMEFRAMES[timeframe]
        ticker = yf.Ticker(symbol)
        df = ticker.history(interval=config["interval"], period=config["period"])

        if df.empty:
            logger.warning(f"No data returned for  {symbol} {timeframe}")
            return None

        df = df.rename(columns={"Open":"open","High":"high",
                                "Low":"low","Close":"close",
                                "Volume":"volume"})
        df = df[["open","high","low","close","volume"]]
        df.index = pd.to_datetime(df.index, utc=True)
        df = df.dropna()

        if timeframe == "H4":
            df = df.resample("4h").agg({
                "open": "first",
                "high":"max",
                "low":"min",
                "close":"last",
                "volume":"sum"
            }).dropna()
        return df
    except Exception as e:
        logger.error(f"Error fetching {symbol} {timeframe}: {e}")
        return None
def fetch_all_pairs() -> dict:
    results = {}

    for symbol in PAIRS:
        label = PAIR_LABELS[symbol]
        results[label] ={}

        for timeframe in TIMEFRAMES.keys():
            df = fetch_ohlcv(symbol, timeframe)
            if df is not None and len(df) >=10:
                results[label][timeframe]=df
    return results

if __name__ == "__main__":
    df = fetch_ohlcv("GBPUSD=X", "D1")
    if df is not None:
        print(df.tail())
        print(f"\nTotal candles: {len(df)}")