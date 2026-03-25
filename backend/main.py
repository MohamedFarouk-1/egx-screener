"""
EGX Upside Screener — FastAPI backend
"""

import csv
import io
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from memo import generate_memo
from screener import CACHE, get_cached_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="EGX Upside Screener API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _background_refresh():
    """Trigger first data load asynchronously at startup."""
    try:
        get_cached_data(force_refresh=True)
        logger.info("Initial data load complete")
    except Exception as exc:
        logger.error("Background refresh failed: %s", exc)


@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=_background_refresh, daemon=True)
    thread.start()


@app.get("/api/health")
def health():
    last = CACHE.get("last_refresh")
    last_str = (
        datetime.fromtimestamp(last, tz=timezone.utc).isoformat()
        if last
        else None
    )
    return {"status": "ok", "last_data_refresh": last_str}


@app.get("/api/screener")
def screener():
    try:
        data = get_cached_data()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Data unavailable: {exc}")
    return data


@app.get("/api/screener/csv")
def screener_csv():
    try:
        data = get_cached_data()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Data unavailable: {exc}")

    stocks = data.get("stocks", [])
    if not stocks:
        raise HTTPException(status_code=404, detail="No data available")

    columns = [
        "rank", "ticker", "name", "sector", "price_egp", "market_cap_egp_b",
        "market_cap_usd_m", "pe", "ev_ebitda", "pb", "revenue_growth_pct",
        "roe_pct", "debt_equity", "current_ratio", "return_52w_pct",
        "composite_score", "score_valuation", "score_growth", "score_quality",
        "score_momentum", "flags", "thesis",
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for stock in stocks:
        row = dict(stock)
        row["flags"] = "|".join(row.get("flags") or [])
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=egx_screener.csv"},
    )


@app.get("/api/screener/memo", response_class=PlainTextResponse)
def screener_memo():
    try:
        data = get_cached_data()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Data unavailable: {exc}")

    memo_text = generate_memo(data)
    return memo_text


# ── Serve React frontend (only in Docker / production) ──────────────────────
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(_static_dir / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        index = _static_dir / "index.html"
        return FileResponse(str(index))
