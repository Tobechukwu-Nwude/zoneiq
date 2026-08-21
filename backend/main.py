import logging
import threading

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from engine.scanner import run_scan, serialize

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ZoneIQ API",
    description="Multi-pair forex scanner using supply and demand zone analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache = {
    "result": None,
    "scanning": False,
}


def _scan_and_cache():
    if _cache["scanning"]:
        logger.info("Scan already running, skipping")
        return

    _cache["scanning"] = True
    try:
        logger.info("Starting scan...")
        raw = run_scan()
        _cache["result"] = serialize(raw)
        logger.info(f"Scan complete: {_cache['result']['setups_found']} setups")
    except Exception as e:
        logger.error(f"Scan failed: {e}")
    finally:
        _cache["scanning"] = False


scheduler = BackgroundScheduler()
scheduler.add_job(_scan_and_cache, "interval", minutes=30, id="scan")
scheduler.start()


@app.on_event("startup")
def startup():
    thread = threading.Thread(target=_scan_and_cache, daemon=True)
    thread.start()
    logger.info("ZoneIQ started, initial scan running")


@app.get("/")
def root():
    return {"status": "ZoneIQ running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "has_data": _cache["result"] is not None,
        "scanning": _cache["scanning"],
    }


@app.get("/scan")
def get_scan():
    if _cache["result"] is None:
        return {
            "status": "scanning" if _cache["scanning"] else "pending",
            "message": "Scan in progress, check back shortly",
            "setups": [],
            "setups_found": 0,
        }

    return {
        "status": "ready",
        "refreshing": _cache["scanning"],
        **_cache["result"],
    }


@app.post("/scan/refresh")
def refresh():
    if _cache["scanning"]:
        return {"status": "already_scanning"}

    thread = threading.Thread(target=_scan_and_cache, daemon=True)
    thread.start()
    return {"status": "triggered"}


@app.get("/pair/{pair}")
def get_pair(pair: str):
    if _cache["result"] is None:
        raise HTTPException(status_code=503, detail="No scan data yet")

    pair = pair.upper()
    biases = _cache["result"]["pair_biases"]

    if pair not in biases:
        raise HTTPException(status_code=404, detail=f"{pair} not found")

    setups = [s for s in _cache["result"]["setups"] if s["pair"] == pair]

    return {"pair": pair, "bias": biases[pair], "setups": setups}