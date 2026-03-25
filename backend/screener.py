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

CACHE: dict[str, Any] = {
    "data": None,
    "last_refresh": None,
}
CACHE_TTL_SECONDS = 6 * 3600  # 6 hours


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
                    # columns are date-ordered newest first
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
            "forward_pe": _safe_float(info.get("forwardPE")),
            "pb": _safe_float(info.get("priceToBook")),
            "roe": _safe_float(info.get("returnOnEquity")),
            "current_ratio": _safe_float(info.get("currentRatio")),
            "debt_equity": _safe_float(info.get("debtToEquity")),
            "ev_ebitda": _safe_float(info.get("enterpriseToEbitda")),
            "return_52w": _safe_float(info.get("52WeekChange")),
            "week52_high": _safe_float(info.get("fiftyTwoWeekHigh")),
            "week52_low": _safe_float(info.get("fiftyTwoWeekLow")),
            "revenue_growth": revenue_growth,
        }
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", symbol, exc)
        return None


def _percentile_rank(series: pd.Series) -> pd.Series:
    """Rank values 0-100, higher value = higher rank. NaN preserved."""
    return series.rank(pct=True) * 100


def _inv_percentile_rank(series: pd.Series) -> pd.Series:
    """Rank values 0-100, lower value = higher rank (inverse). NaN preserved."""
    return (1 - series.rank(pct=True)) * 100


def _fill_missing(df: pd.DataFrame, col: str) -> pd.Series:
    """Fill NaN with sector median, then universe median."""
    filled = df[col].copy()
    sector_med = df.groupby("sector")[col].transform("median")
    univ_med = df[col].median()
    filled = filled.fillna(sector_med).fillna(univ_med)
    return filled


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

    # Momentum
    ret_str = f"{ret52:.1f}%" if ret52 is not None else "strong"
    return f"Momentum play in {sector}: {ret_str} 52-week return with improving fundamentals"


def _get_usd_egp_rate() -> float:
    try:
        ticker = yf.Ticker("USDEGP=X")
        info = ticker.info or {}
        rate = _safe_float(info.get("regularMarketPrice") or info.get("bid"))
        if rate and rate > 1:
            return rate
    except Exception:
        pass
    return 50.5  # fallback


def _get_egx30_level() -> Optional[float]:
    try:
        ticker = yf.Ticker("^CASE30")
        info = ticker.info or {}
        level = _safe_float(info.get("regularMarketPrice") or info.get("previousClose"))
        if level:
            return level
    except Exception:
        pass
    return None


def run_screener() -> dict:
    logger.info("Starting EGX screener data pipeline for %d tickers", len(EGX_TICKERS))
    raw_records = []

    for symbol in EGX_TICKERS:
        logger.debug("Fetching %s", symbol)
        rec = _fetch_ticker_data(symbol)
        if rec:
            raw_records.append(rec)
        time.sleep(0.15)  # gentle rate limiting

    if not raw_records:
        logger.error("No data returned from yfinance")
        return {"stocks": [], "sector_summary": [], "universe_size": 0}

    df = pd.DataFrame(raw_records)
    logger.info("Universe after filtering: %d stocks", len(df))

    # --- Fill missing values ---
    for col in ["pe", "ev_ebitda", "pb", "roe", "current_ratio", "debt_equity", "return_52w", "revenue_growth"]:
        df[col] = _fill_missing(df, col)

    # Convert ROE from decimal (yfinance) to pct
    if df["roe"].abs().median() < 5:
        df["roe"] = df["roe"] * 100

    # Convert 52w return from decimal to pct
    if df["return_52w"].abs().median() < 5:
        df["return_52w"] = df["return_52w"] * 100

    # --- Clip extreme outliers (winsorise at 2.5/97.5 pct) ---
    for col in ["pe", "ev_ebitda", "pb", "roe", "debt_equity"]:
        lo, hi = df[col].quantile(0.025), df[col].quantile(0.975)
        df[col] = df[col].clip(lo, hi)

    # --- Scoring ---
    # Only use positive PE/EV for valuation rank
    df["pe_for_rank"] = df["pe"].where(df["pe"] > 0, other=np.nan)
    df["pe_for_rank"] = _fill_missing(df.assign(sector=df["sector"]), "pe_for_rank") if "pe_for_rank" in df else df["pe"]
    df["ev_for_rank"] = df["ev_ebitda"].where(df["ev_ebitda"] > 0, other=np.nan)
    df["ev_for_rank"] = df["ev_for_rank"].fillna(df["ev_ebitda"])

    val_pe = _inv_percentile_rank(df["pe_for_rank"])
    val_ev = _inv_percentile_rank(df["ev_for_rank"])
    val_pb = _inv_percentile_rank(df["pb"])
    df["score_valuation"] = (val_pe + val_ev + val_pb) / 3

    grow_rev = _percentile_rank(df["revenue_growth"])
    grow_roe = _percentile_rank(df["roe"])
    df["score_growth"] = (grow_rev + grow_roe) / 2

    qual_roe = _percentile_rank(df["roe"])
    qual_de = _inv_percentile_rank(df["debt_equity"])
    qual_cr = _percentile_rank(df["current_ratio"])
    df["score_quality"] = (qual_roe + qual_de + qual_cr) / 3

    df["score_momentum"] = _percentile_rank(df["return_52w"])

    df["composite_score"] = (
        0.35 * df["score_valuation"]
        + 0.30 * df["score_growth"]
        + 0.25 * df["score_quality"]
        + 0.10 * df["score_momentum"]
    )

    df = df.sort_values("composite_score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    # --- Flags ---
    def get_flags(row):
        flags = []
        pb_raw = row.get("pb")
        if pb_raw is not None and pb_raw < 1.0:
            flags.append("deep_value")
        de = row.get("debt_equity")
        ev_eb = row.get("ev_ebitda")
        if (de is not None and de > 2.0) or (ev_eb is not None and ev_eb > 4.0 and de is not None and de > 1.0):
            flags.append("overleveraged")
        cr = row.get("current_ratio")
        if cr is not None and cr < 1.0:
            flags.append("liquidity_risk")
        return flags

    # --- FX rate ---
    usd_egp = _get_usd_egp_rate()
    egx30 = _get_egx30_level()

    # --- Build output ---
    stocks = []
    for _, row in df.iterrows():
        mkt_cap = row.get("market_cap")
        mkt_cap_egp_b = (mkt_cap / 1e9) if mkt_cap else None
        mkt_cap_usd_m = (mkt_cap / usd_egp / 1e6) if mkt_cap else None

        # Re-fetch raw (unfilled) values for display
        raw_rec = next((r for r in raw_records if r["ticker"] == row["ticker"]), {})

        stock_row = row.to_dict()
        stock_row.update({
            "pe": raw_rec.get("pe"),
            "ev_ebitda": raw_rec.get("ev_ebitda"),
            "pb": raw_rec.get("pb"),
            "roe": raw_rec.get("roe"),
            "current_ratio": raw_rec.get("current_ratio"),
            "debt_equity": raw_rec.get("debt_equity"),
            "return_52w": raw_rec.get("return_52w"),
            "revenue_growth": raw_rec.get("revenue_growth"),
        })

        roe_val = raw_rec.get("roe")
        if roe_val is not None and abs(roe_val) < 5:
            roe_val = roe_val * 100
        ret52_val = raw_rec.get("return_52w")
        if ret52_val is not None and abs(ret52_val) < 5:
            ret52_val = ret52_val * 100

        record = {
            "rank": int(row["rank"]),
            "ticker": row["ticker"],
            "name": row["name"],
            "sector": row["sector"],
            "price_egp": round(float(row["price_egp"]), 2),
            "market_cap_egp_b": round(mkt_cap_egp_b, 2) if mkt_cap_egp_b is not None else None,
            "market_cap_usd_m": round(mkt_cap_usd_m, 1) if mkt_cap_usd_m is not None else None,
            "pe": round(raw_rec.get("pe"), 2) if raw_rec.get("pe") is not None else None,
            "ev_ebitda": round(raw_rec.get("ev_ebitda"), 2) if raw_rec.get("ev_ebitda") is not None else None,
            "pb": round(raw_rec.get("pb"), 2) if raw_rec.get("pb") is not None else None,
            "revenue_growth_pct": round(raw_rec.get("revenue_growth"), 1) if raw_rec.get("revenue_growth") is not None else None,
            "roe_pct": round(roe_val, 1) if roe_val is not None else None,
            "debt_equity": round(raw_rec.get("debt_equity"), 2) if raw_rec.get("debt_equity") is not None else None,
            "current_ratio": round(raw_rec.get("current_ratio"), 2) if raw_rec.get("current_ratio") is not None else None,
            "return_52w_pct": round(ret52_val, 1) if ret52_val is not None else None,
            "composite_score": round(float(row["composite_score"]), 1),
            "score_valuation": round(float(row["score_valuation"]), 1),
            "score_growth": round(float(row["score_growth"]), 1),
            "score_quality": round(float(row["score_quality"]), 1),
            "score_momentum": round(float(row["score_momentum"]), 1),
            "flags": get_flags({"pb": raw_rec.get("pb"), "debt_equity": raw_rec.get("debt_equity"), "ev_ebitda": raw_rec.get("ev_ebitda"), "current_ratio": raw_rec.get("current_ratio")}),
        }
        record["thesis"] = _generate_thesis(pd.Series(record))
        stocks.append(record)

    # --- Sector summary ---
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
        "stocks": stocks,
        "sector_summary": sector_summary,
    }


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
