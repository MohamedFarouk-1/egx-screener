"""
EGX Stock Screener — Data pipeline and scoring engine
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

EGX_TICKERS = [
    "COMI.CA", "SWDY.CA", "TMGH.CA", "ETEL.CA", "MFPC.CA", "EAST.CA",
    "EGAL.CA", "ABUK.CA", "QNBE.CA", "ALCN.CA", "EFIH.CA", "FWRY.CA",
    "HDBK.CA", "ORAS.CA", "EMFD.CA", "ADIB.CA", "EFID.CA", "HRHO.CA",
    "JUFO.CA", "GBCO.CA", "PHDC.CA", "EGCH.CA", "ORHD.CA", "SKPC.CA",
    "CLHO.CA", "ARCC.CA", "TAQA.CA", "ORWE.CA", "PHAR.CA", "ISPH.CA",
    "CIRA.CA", "AMOC.CA", "DOMT.CA", "SUGR.CA", "OLFI.CA", "MICH.CA",
    "EXPA.CA", "OCDI.CA", "MASR.CA", "LCSW.CA", "ENGC.CA", "KZPC.CA",
    "NAPR.CA", "ASCM.CA", "ECAP.CA", "SCEM.CA", "MBSC.CA", "MCQE.CA",
    "EFIC.CA", "MTIE.CA", "VALU.CA", "HELI.CA", "CSAG.CA",
]

# Static fallback data (stockanalysis.com, March 2026)
FALLBACK_DATA = [
    {"ticker": "COMI", "name": "Commercial International Bank (CIB)", "sector": "Financial Services", "price": 126.00, "market_cap_b": 410.4, "pe": 8.5, "ev_ebitda": 6.0, "pb": 2.8, "revenue_growth_pct": 12.0, "roe_pct": 22.0, "debt_equity": 0.5, "current_ratio": 1.2, "return_52w_pct": 48.0},
    {"ticker": "SWDY", "name": "El Sewedy Electric", "sector": "Industrials", "price": 78.00, "market_cap_b": 169.2, "pe": 10.4, "ev_ebitda": 5.5, "pb": 3.6, "revenue_growth_pct": 34.0, "roe_pct": 34.7, "debt_equity": 0.88, "current_ratio": 1.20, "return_52w_pct": 61.4},
    {"ticker": "TMGH", "name": "Talaat Moustafa Group", "sector": "Real Estate", "price": 80.59, "market_cap_b": 162.8, "pe": 10.7, "ev_ebitda": 11.5, "pb": 1.6, "revenue_growth_pct": 67.0, "roe_pct": 14.6, "debt_equity": 0.25, "current_ratio": 1.38, "return_52w_pct": 49.1},
    {"ticker": "ETEL", "name": "Telecom Egypt", "sector": "Telecom", "price": 88.00, "market_cap_b": 150.2, "pe": 16.8, "ev_ebitda": 2.9, "pb": 4.2, "revenue_growth_pct": 25.0, "roe_pct": 25.1, "debt_equity": 1.86, "current_ratio": 0.53, "return_52w_pct": 15.5},
    {"ticker": "MFPC", "name": "Misr Fertilizer (MOPCO)", "sector": "Basic Materials", "price": 40.53, "market_cap_b": 116.3, "pe": 7.9, "ev_ebitda": 6.1, "pb": 2.1, "revenue_growth_pct": 18.0, "roe_pct": 26.3, "debt_equity": 0.0, "current_ratio": 1.52, "return_52w_pct": 12.1},
    {"ticker": "EAST", "name": "Eastern Company (Tobacco)", "sector": "Consumer Defensive", "price": 37.85, "market_cap_b": 113.6, "pe": 6.5, "ev_ebitda": 5.8, "pb": 4.5, "revenue_growth_pct": 82.8, "roe_pct": 45.0, "debt_equity": 0.2, "current_ratio": 1.10, "return_52w_pct": 70.0},
    {"ticker": "EGAL", "name": "Egypt Aluminum", "sector": "Basic Materials", "price": 271.03, "market_cap_b": 111.8, "pe": 5.2, "ev_ebitda": 4.8, "pb": 2.0, "revenue_growth_pct": 55.0, "roe_pct": 38.0, "debt_equity": 0.1, "current_ratio": 1.80, "return_52w_pct": 85.0},
    {"ticker": "ABUK", "name": "Abu Qir Fertilizers", "sector": "Basic Materials", "price": 78.64, "market_cap_b": 99.2, "pe": 6.8, "ev_ebitda": 5.2, "pb": 1.9, "revenue_growth_pct": 15.0, "roe_pct": 28.0, "debt_equity": 0.05, "current_ratio": 1.90, "return_52w_pct": 18.0},
    {"ticker": "QNBE", "name": "QNB Al Ahli (Egypt)", "sector": "Financial Services", "price": 41.53, "market_cap_b": 89.5, "pe": 5.0, "ev_ebitda": 5.0, "pb": 1.5, "revenue_growth_pct": 30.0, "roe_pct": 18.0, "debt_equity": 0.5, "current_ratio": 1.1, "return_52w_pct": 22.0},
    {"ticker": "ALCN", "name": "Alexandria Container & Cargo", "sector": "Industrials", "price": 25.30, "market_cap_b": 72.4, "pe": 14.0, "ev_ebitda": 11.0, "pb": 5.5, "revenue_growth_pct": 20.0, "roe_pct": 30.0, "debt_equity": 0.3, "current_ratio": 1.30, "return_52w_pct": 50.0},
    {"ticker": "FWRY", "name": "Fawry", "sector": "Technology", "price": 18.20, "market_cap_b": 60.3, "pe": 29.3, "ev_ebitda": 20.9, "pb": 13.6, "revenue_growth_pct": 40.0, "roe_pct": 46.3, "debt_equity": 0.47, "current_ratio": 1.33, "return_52w_pct": 143.8},
    {"ticker": "HDBK", "name": "Housing & Development Bank", "sector": "Financial Services", "price": 110.32, "market_cap_b": 58.6, "pe": 4.8, "ev_ebitda": 4.8, "pb": 1.2, "revenue_growth_pct": 35.0, "roe_pct": 20.0, "debt_equity": 0.5, "current_ratio": 1.1, "return_52w_pct": 25.0},
    {"ticker": "ORAS", "name": "Orascom Construction", "sector": "Industrials", "price": 467.57, "market_cap_b": 52.3, "pe": 12.5, "ev_ebitda": 6.0, "pb": 1.8, "revenue_growth_pct": 22.0, "roe_pct": 15.0, "debt_equity": 1.0, "current_ratio": 1.15, "return_52w_pct": 30.0},
    {"ticker": "EMFD", "name": "Emaar Misr", "sector": "Real Estate", "price": 9.00, "market_cap_b": 49.0, "pe": 8.0, "ev_ebitda": 6.5, "pb": 1.0, "revenue_growth_pct": 45.0, "roe_pct": 18.0, "debt_equity": 0.3, "current_ratio": 1.40, "return_52w_pct": 20.0},
    {"ticker": "ADIB", "name": "Abu Dhabi Islamic Bank Egypt", "sector": "Financial Services", "price": 37.81, "market_cap_b": 45.4, "pe": 4.2, "ev_ebitda": 4.2, "pb": 1.8, "revenue_growth_pct": 28.0, "roe_pct": 32.0, "debt_equity": 0.4, "current_ratio": 1.1, "return_52w_pct": 15.0},
    {"ticker": "EFID", "name": "Edita Food Industries", "sector": "Consumer Defensive", "price": 27.50, "market_cap_b": 38.2, "pe": 16.0, "ev_ebitda": 12.0, "pb": 5.0, "revenue_growth_pct": 35.0, "roe_pct": 22.0, "debt_equity": 0.5, "current_ratio": 1.25, "return_52w_pct": 40.0},
    {"ticker": "HRHO", "name": "EFG Holding", "sector": "Financial Services", "price": 25.78, "market_cap_b": 37.5, "pe": 6.0, "ev_ebitda": 6.0, "pb": 1.0, "revenue_growth_pct": 25.0, "roe_pct": 16.0, "debt_equity": 0.8, "current_ratio": 1.1, "return_52w_pct": 28.0},
    {"ticker": "JUFO", "name": "Juhayna Food Industries", "sector": "Consumer Defensive", "price": 26.67, "market_cap_b": 31.4, "pe": 12.0, "ev_ebitda": 8.5, "pb": 3.5, "revenue_growth_pct": 30.0, "roe_pct": 20.0, "debt_equity": 0.4, "current_ratio": 1.60, "return_52w_pct": 55.0},
    {"ticker": "GBCO", "name": "GB Auto (GB Corp)", "sector": "Consumer Cyclical", "price": 26.84, "market_cap_b": 29.1, "pe": 4.5, "ev_ebitda": 5.0, "pb": 1.2, "revenue_growth_pct": 40.0, "roe_pct": 28.0, "debt_equity": 2.5, "current_ratio": 1.10, "return_52w_pct": 45.0},
    {"ticker": "PHDC", "name": "Palm Hills Developments", "sector": "Real Estate", "price": 8.67, "market_cap_b": 24.8, "pe": 5.5, "ev_ebitda": 7.0, "pb": 0.9, "revenue_growth_pct": 55.0, "roe_pct": 12.0, "debt_equity": 1.0, "current_ratio": 1.20, "return_52w_pct": 35.0},
    {"ticker": "EGCH", "name": "Egyptian Chemical Industries", "sector": "Basic Materials", "price": 12.55, "market_cap_b": 24.9, "pe": 7.6, "ev_ebitda": 13.9, "pb": 2.1, "revenue_growth_pct": 28.0, "roe_pct": 27.6, "debt_equity": 0.85, "current_ratio": 3.47, "return_52w_pct": 65.8},
    {"ticker": "ORHD", "name": "Orascom Development Egypt", "sector": "Real Estate", "price": 23.60, "market_cap_b": 26.7, "pe": 9.0, "ev_ebitda": 8.0, "pb": 1.5, "revenue_growth_pct": 38.0, "roe_pct": 15.0, "debt_equity": 0.8, "current_ratio": 1.30, "return_52w_pct": 20.0},
    {"ticker": "SKPC", "name": "Sidi Kerir Petrochemicals", "sector": "Energy", "price": 17.53, "market_cap_b": 19.9, "pe": 6.5, "ev_ebitda": 4.5, "pb": 1.8, "revenue_growth_pct": 20.0, "roe_pct": 22.0, "debt_equity": 0.3, "current_ratio": 1.40, "return_52w_pct": 15.0},
    {"ticker": "ARCC", "name": "Arabian Cement", "sector": "Basic Materials", "price": 49.77, "market_cap_b": 18.8, "pe": 5.0, "ev_ebitda": 4.0, "pb": 1.0, "revenue_growth_pct": 30.0, "roe_pct": 25.0, "debt_equity": 0.4, "current_ratio": 1.50, "return_52w_pct": 22.0},
    {"ticker": "CLHO", "name": "Cleopatra Hospitals", "sector": "Healthcare", "price": 12.96, "market_cap_b": 18.8, "pe": 15.0, "ev_ebitda": 10.0, "pb": 3.0, "revenue_growth_pct": 25.0, "roe_pct": 18.0, "debt_equity": 0.8, "current_ratio": 1.20, "return_52w_pct": 30.0},
    {"ticker": "EXPA", "name": "Export Development Bank", "sector": "Financial Services", "price": 16.00, "market_cap_b": 21.8, "pe": 3.4, "ev_ebitda": 3.4, "pb": 0.7, "revenue_growth_pct": 20.0, "roe_pct": 28.8, "debt_equity": 0.07, "current_ratio": 1.1, "return_52w_pct": 20.5},
    {"ticker": "MICH", "name": "Misr Chemical Industries", "sector": "Basic Materials", "price": 30.22, "market_cap_b": 3.3, "pe": 4.6, "ev_ebitda": 4.7, "pb": 2.7, "revenue_growth_pct": 15.0, "roe_pct": 57.9, "debt_equity": 0.22, "current_ratio": 3.40, "return_52w_pct": 8.4},
    {"ticker": "AMOC", "name": "Alexandria Mineral Oils", "sector": "Energy", "price": 7.61, "market_cap_b": 9.7, "pe": 3.5, "ev_ebitda": 2.5, "pb": 0.8, "revenue_growth_pct": 25.0, "roe_pct": 30.0, "debt_equity": 0.2, "current_ratio": 1.60, "return_52w_pct": 10.0},
    {"ticker": "MASR", "name": "Madinet Masr Housing", "sector": "Real Estate", "price": 5.30, "market_cap_b": 11.3, "pe": 4.0, "ev_ebitda": 3.5, "pb": 0.6, "revenue_growth_pct": 50.0, "roe_pct": 20.0, "debt_equity": 0.2, "current_ratio": 1.50, "return_52w_pct": 55.0},
    {"ticker": "LCSW", "name": "Lecico Egypt", "sector": "Industrials", "price": 24.93, "market_cap_b": 2.0, "pe": 3.5, "ev_ebitda": 3.0, "pb": 0.7, "revenue_growth_pct": 35.0, "roe_pct": 18.0, "debt_equity": 0.5, "current_ratio": 1.30, "return_52w_pct": 15.0},
    {"ticker": "KZPC", "name": "Kafr El Zayat Pesticides", "sector": "Basic Materials", "price": 9.95, "market_cap_b": 2.4, "pe": 4.0, "ev_ebitda": 3.5, "pb": 0.8, "revenue_growth_pct": 30.0, "roe_pct": 22.0, "debt_equity": 0.8, "current_ratio": 1.10, "return_52w_pct": 12.0},
]

CACHE: dict[str, Any] = {
    "data": None,
    "last_refresh": None,
}
CACHE_TTL_SECONDS = 6 * 3600  # 6 hours
LIVE_MIN_STOCKS = 10  # fall back to static if yfinance returns fewer than this


def _safe_float(val) -> Optional[float]:
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return None
        return float(val)
    except Exception:
        return None


def _fetch_ticker_data(symbol: str) -> Optional[dict]:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}

        price = _safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
        if price is None or price < 1.0:
            return None

        # Revenue growth from financials
        revenue_growth = None
        try:
            fin = ticker.financials
            if fin is not None and not fin.empty and "Total Revenue" in fin.index:
                rev_row = fin.loc["Total Revenue"].dropna()
                if len(rev_row) >= 2:
                    latest = float(rev_row.iloc[0])
                    prior = float(rev_row.iloc[1])
                    if prior and prior != 0:
                        revenue_growth = (latest - prior) / abs(prior) * 100.0
        except Exception:
            pass

        short_ticker = symbol.replace(".CA", "")
        return {
            "ticker": short_ticker,
            "name": info.get("longName") or info.get("shortName") or short_ticker,
            "sector": info.get("sector") or "Unknown",
            "price_egp": price,
            "market_cap": _safe_float(info.get("marketCap")),
            "pe": _safe_float(info.get("trailingPE")),
            "pb": _safe_float(info.get("priceToBook")),
            "roe": _safe_float(info.get("returnOnEquity")),
            "current_ratio": _safe_float(info.get("currentRatio")),
            "debt_equity": _safe_float(info.get("debtToEquity")),
            "ev_ebitda": _safe_float(info.get("enterpriseToEbitda")),
            "return_52w": _safe_float(info.get("52WeekChange")),
            "revenue_growth": revenue_growth,
        }
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", symbol, exc)
        return None


def _fetch_live_data() -> list[dict]:
    """Try yfinance with 3-second delays. Returns normalised raw records."""
    raw_records = []
    for symbol in EGX_TICKERS:
        rec = _fetch_ticker_data(symbol)
        if rec:
            raw_records.append(rec)
        time.sleep(3)
    return raw_records


def _normalise_fallback() -> list[dict]:
    """Convert FALLBACK_DATA entries into the same schema as live records."""
    records = []
    for row in FALLBACK_DATA:
        records.append({
            "ticker": row["ticker"],
            "name": row["name"],
            "sector": row["sector"],
            "price_egp": row["price"],
            "market_cap": row["market_cap_b"] * 1e9,
            "pe": row["pe"],
            "pb": row["pb"],
            "roe": row["roe_pct"],          # already in pct form
            "current_ratio": row["current_ratio"],
            "debt_equity": row["debt_equity"],
            "ev_ebitda": row["ev_ebitda"],
            "return_52w": row["return_52w_pct"],  # already in pct form
            "revenue_growth": row["revenue_growth_pct"],
        })
    return records


def _percentile_rank(series: pd.Series) -> pd.Series:
    return series.rank(pct=True) * 100


def _inv_percentile_rank(series: pd.Series) -> pd.Series:
    return (1 - series.rank(pct=True)) * 100


def _fill_missing(df: pd.DataFrame, col: str) -> pd.Series:
    filled = df[col].copy()
    sector_med = df.groupby("sector")[col].transform("median")
    univ_med = df[col].median()
    return filled.fillna(sector_med).fillna(univ_med)


def _generate_thesis(row: pd.Series) -> str:
    scores = {
        "Valuation": row.get("score_valuation", 0) or 0,
        "Growth": row.get("score_growth", 0) or 0,
        "Quality": row.get("score_quality", 0) or 0,
        "Momentum": row.get("score_momentum", 0) or 0,
    }
    top_dim = max(scores, key=scores.get)
    sector = row.get("sector", "Unknown")
    pe = row.get("pe")
    pb = row.get("pb")
    ev_ebitda = row.get("ev_ebitda")
    roe = row.get("roe_pct")
    rev_g = row.get("revenue_growth_pct")
    ret52 = row.get("return_52w_pct")
    de = row.get("debt_equity")

    if top_dim == "Valuation":
        parts = []
        if pe and pe > 0:
            parts.append(f"{pe:.1f}x PE")
        if ev_ebitda and ev_ebitda > 0:
            parts.append(f"{ev_ebitda:.1f}x EV/EBITDA")
        if pb and pb > 0:
            parts.append(f"{pb:.1f}x P/B")
        metrics = ", ".join(parts) if parts else "attractive multiples"
        return f"Deep value in {sector}: {metrics}, well below sector peers"

    if top_dim == "Growth":
        parts = []
        if rev_g is not None:
            parts.append(f"{rev_g:.1f}% revenue growth")
        if roe is not None:
            parts.append(f"{roe:.1f}% ROE")
        metrics = " and ".join(parts) if parts else "strong growth metrics"
        return f"Growth compounder in {sector}: {metrics}"

    if top_dim == "Quality":
        parts = []
        if roe is not None:
            parts.append(f"{roe:.1f}% ROE")
        if de is not None and de < 0.5:
            parts.append("pristine balance sheet")
        metrics = ", ".join(parts) if parts else "high quality metrics"
        return f"Quality franchise in {sector}: {metrics}"

    ret_str = f"{ret52:.1f}%" if ret52 is not None else "strong"
    return f"Momentum play in {sector}: {ret_str} 52-week return with improving fundamentals"


def _get_usd_egp_rate() -> float:
    try:
        info = yf.Ticker("USDEGP=X").info or {}
        rate = _safe_float(info.get("regularMarketPrice") or info.get("bid"))
        if rate and rate > 1:
            return rate
    except Exception:
        pass
    return 50.5


def _get_egx30_level() -> Optional[float]:
    try:
        info = yf.Ticker("^CASE30").info or {}
        level = _safe_float(info.get("regularMarketPrice") or info.get("previousClose"))
        if level:
            return level
    except Exception:
        pass
    return None


def _score_and_build(raw_records: list[dict], data_source: str, usd_egp: float, egx30: Optional[float]) -> dict:
    """Run the scoring engine on normalised raw_records and return the full API payload."""
    df = pd.DataFrame(raw_records)
    logger.info("Scoring %d stocks (source: %s)", len(df), data_source)

    is_live = data_source == "live"

    for col in ["pe", "ev_ebitda", "pb", "roe", "current_ratio", "debt_equity", "return_52w", "revenue_growth"]:
        df[col] = _fill_missing(df, col)

    # yfinance returns ROE/52w as decimals; static data is already in pct
    if is_live:
        if df["roe"].abs().median() < 5:
            df["roe"] = df["roe"] * 100
        if df["return_52w"].abs().median() < 5:
            df["return_52w"] = df["return_52w"] * 100

    for col in ["pe", "ev_ebitda", "pb", "roe", "debt_equity"]:
        lo, hi = df[col].quantile(0.025), df[col].quantile(0.975)
        df[col] = df[col].clip(lo, hi)

    df["pe_for_rank"] = df["pe"].where(df["pe"] > 0, other=np.nan).fillna(df["pe"])
    df["ev_for_rank"] = df["ev_ebitda"].where(df["ev_ebitda"] > 0, other=np.nan).fillna(df["ev_ebitda"])

    df["score_valuation"] = (_inv_percentile_rank(df["pe_for_rank"]) + _inv_percentile_rank(df["ev_for_rank"]) + _inv_percentile_rank(df["pb"])) / 3
    df["score_growth"] = (_percentile_rank(df["revenue_growth"]) + _percentile_rank(df["roe"])) / 2
    df["score_quality"] = (_percentile_rank(df["roe"]) + _inv_percentile_rank(df["debt_equity"]) + _percentile_rank(df["current_ratio"])) / 3
    df["score_momentum"] = _percentile_rank(df["return_52w"])

    df["composite_score"] = (
        0.35 * df["score_valuation"]
        + 0.30 * df["score_growth"]
        + 0.25 * df["score_quality"]
        + 0.10 * df["score_momentum"]
    )

    df = df.sort_values("composite_score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    def get_flags(r):
        flags = []
        if r.get("pb") is not None and r["pb"] < 1.0:
            flags.append("deep_value")
        de = r.get("debt_equity")
        if de is not None and de > 2.0:
            flags.append("overleveraged")
        cr = r.get("current_ratio")
        if cr is not None and cr < 1.0:
            flags.append("liquidity_risk")
        return flags

    stocks = []
    for _, row in df.iterrows():
        mkt_cap = row.get("market_cap")
        mkt_cap_egp_b = (mkt_cap / 1e9) if mkt_cap else None
        mkt_cap_usd_m = (mkt_cap / usd_egp / 1e6) if mkt_cap else None

        raw = next((r for r in raw_records if r["ticker"] == row["ticker"]), {})

        # Display ROE/52w in pct regardless of source
        roe_val = raw.get("roe")
        if is_live and roe_val is not None and abs(roe_val) < 5:
            roe_val = roe_val * 100
        ret52_val = raw.get("return_52w")
        if is_live and ret52_val is not None and abs(ret52_val) < 5:
            ret52_val = ret52_val * 100

        record = {
            "rank": int(row["rank"]),
            "ticker": row["ticker"],
            "name": row["name"],
            "sector": row["sector"],
            "price_egp": round(float(row["price_egp"]), 2),
            "market_cap_egp_b": round(mkt_cap_egp_b, 2) if mkt_cap_egp_b is not None else None,
            "market_cap_usd_m": round(mkt_cap_usd_m, 1) if mkt_cap_usd_m is not None else None,
            "pe": round(raw["pe"], 2) if raw.get("pe") is not None else None,
            "ev_ebitda": round(raw["ev_ebitda"], 2) if raw.get("ev_ebitda") is not None else None,
            "pb": round(raw["pb"], 2) if raw.get("pb") is not None else None,
            "revenue_growth_pct": round(raw["revenue_growth"], 1) if raw.get("revenue_growth") is not None else None,
            "roe_pct": round(roe_val, 1) if roe_val is not None else None,
            "debt_equity": round(raw["debt_equity"], 2) if raw.get("debt_equity") is not None else None,
            "current_ratio": round(raw["current_ratio"], 2) if raw.get("current_ratio") is not None else None,
            "return_52w_pct": round(ret52_val, 1) if ret52_val is not None else None,
            "composite_score": round(float(row["composite_score"]), 1),
            "score_valuation": round(float(row["score_valuation"]), 1),
            "score_growth": round(float(row["score_growth"]), 1),
            "score_quality": round(float(row["score_quality"]), 1),
            "score_momentum": round(float(row["score_momentum"]), 1),
            "flags": get_flags(raw),
        }
        record["thesis"] = _generate_thesis(pd.Series(record))
        stocks.append(record)

    df_out = pd.DataFrame(stocks)
    sector_summary = []
    for sector, grp in df_out.groupby("sector"):
        def med(col):
            vals = grp[col].dropna()
            return round(float(vals.median()), 2) if len(vals) else None
        sector_summary.append({
            "sector": sector,
            "count": len(grp),
            "median_pe": med("pe"),
            "median_roe": med("roe_pct"),
            "median_composite": med("composite_score"),
        })
    sector_summary.sort(key=lambda x: x["median_composite"] or 0, reverse=True)

    return {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "universe_size": len(stocks),
        "usd_egp_rate": usd_egp,
        "egx30_level": egx30,
        "data_source": data_source,
        "stocks": stocks,
        "sector_summary": sector_summary,
    }


def run_screener() -> dict:
    logger.info("Starting EGX screener pipeline (attempting live yfinance)")

    # Try live first
    live_records = _fetch_live_data()

    if len(live_records) >= LIVE_MIN_STOCKS:
        logger.info("Live data: %d stocks fetched", len(live_records))
        data_source = "live"
        raw_records = live_records
    else:
        logger.warning(
            "yfinance returned only %d stocks (< %d threshold) — falling back to static data",
            len(live_records), LIVE_MIN_STOCKS,
        )
        data_source = "static (Mar 2026)"
        raw_records = _normalise_fallback()

    # Best-effort FX / index (short timeout, non-blocking)
    usd_egp = _get_usd_egp_rate()
    egx30 = _get_egx30_level()

    return _score_and_build(raw_records, data_source, usd_egp, egx30)


def get_cached_data(force_refresh: bool = False) -> dict:
    now = time.time()
    last = CACHE.get("last_refresh")
    if force_refresh or last is None or (now - last) > CACHE_TTL_SECONDS:
        logger.info("Cache miss — running screener pipeline")
        try:
            result = run_screener()
            CACHE["data"] = result
            CACHE["last_refresh"] = now
        except Exception as exc:
            logger.error("Screener pipeline failed: %s", exc)
            if CACHE.get("data"):
                logger.warning("Serving stale cache due to error")
            else:
                raise
    return CACHE["data"]
