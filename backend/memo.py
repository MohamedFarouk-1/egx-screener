"""
Investment memo generator for EGX screener
"""

from datetime import date


def generate_memo(data: dict) -> str:
    stocks = data.get("stocks", [])
    sector_summary = data.get("sector_summary", [])
    usd_egp = data.get("usd_egp_rate", 50.5)
    egx30 = data.get("egx30_level")
    today = date.today().strftime("%B %d, %Y")
    universe = data.get("universe_size", 0)

    egx30_str = f"EGX30 at {egx30:,.0f}" if egx30 else "EGX30 levels"

    # --- Paragraph 1: Macro context ---
    para1 = (
        f"EGX INVESTMENT MEMO — {today}\n\n"
        f"MACRO CONTEXT\n"
        f"The Egyptian Exchange continues to trade at a significant discount to emerging market peers following the "
        f"EGP devaluations of 2022-2024, which collectively erased roughly 60% of dollar-denominated purchasing power "
        f"against the US dollar (current rate: ~{usd_egp:.1f} EGP/USD). With {egx30_str}, the market has partially "
        f"recovered in nominal EGP terms, though real USD returns remain compressed for foreign investors. The Central "
        f"Bank of Egypt (CBE) has maintained an elevated policy rate environment — currently above 27% — to anchor "
        f"inflation expectations as CPI runs in the high double digits. This creates a high nominal hurdle rate for "
        f"equities but also historically cheap valuations on a price-to-book and EV/EBITDA basis. Key tail risks include "
        f"further FX adjustment, subsidy reform pace, and geopolitical spillovers from the region. Many EGX names carry "
        f"thin free floats (<20%), related-party transaction risk common in Egyptian conglomerates, and data lag versus "
        f"Arabic EFSA filings — investors should verify fundamentals independently."
    )

    # --- Paragraph 2: Cheapest sectors ---
    top_sectors = sector_summary[:3] if len(sector_summary) >= 3 else sector_summary
    sector_lines = []
    for s in top_sectors:
        pe_str = f"{s['median_pe']:.1f}x PE" if s.get("median_pe") else "N/A PE"
        roe_str = f"{s['median_roe']:.1f}% median ROE" if s.get("median_roe") else "N/A ROE"
        sector_lines.append(
            f"{s['sector']} ({s['count']} stocks, {pe_str}, {roe_str}, composite {s.get('median_composite', 0):.0f}/100)"
        )

    para2 = (
        f"SECTOR ANALYSIS\n"
        f"Our quantitative screen of {universe} EGX-listed stocks identifies the following sectors as offering the "
        f"best risk-adjusted upside on a composite valuation/growth/quality/momentum basis:\n\n"
        + "\n".join(f"  {i+1}. {line}" for i, line in enumerate(sector_lines))
        + f"\n\nThese sectors score highest because they combine below-market multiples with sustained profitability "
        f"despite the inflationary environment. Consumer staples and basic materials names have been able to pass "
        f"through cost inflation via price increases, protecting margins. Financial sector banks benefit from wide "
        f"net interest margins in the high-rate environment. Technology and healthcare names with local revenue streams "
        f"are somewhat insulated from FX drag on earnings. Investors should be cautious of sectors with high USD-cost "
        f"input exposure (industrials importing raw materials) and real estate developers whose backlog pricing may "
        f"not fully reflect current construction costs."
    )

    # --- Paragraph 3: Top 3 conviction picks ---
    top3 = stocks[:3] if len(stocks) >= 3 else stocks
    pick_lines = []
    for s in top3:
        pe_str = f"{s['pe']:.1f}x PE" if s.get("pe") else ""
        pb_str = f"{s['pb']:.1f}x P/B" if s.get("pb") else ""
        roe_str = f"{s['roe_pct']:.1f}% ROE" if s.get("roe_pct") else ""
        ev_str = f"{s['ev_ebitda']:.1f}x EV/EBITDA" if s.get("ev_ebitda") else ""
        metrics = ", ".join(x for x in [pe_str, ev_str, pb_str, roe_str] if x)
        flag_note = " [FLAGS: " + ", ".join(s.get("flags", [])) + "]" if s.get("flags") else ""
        pick_lines.append(
            f"  #{s['rank']} {s['ticker']} ({s['name']}, {s['sector']}) — "
            f"Composite Score {s['composite_score']:.0f}/100. {metrics}. "
            f"{s.get('thesis', '')}{flag_note}"
        )

    para3 = (
        f"TOP CONVICTION PICKS\n"
        f"The three highest-ranked stocks by composite score are:\n\n"
        + "\n\n".join(pick_lines)
        + f"\n\nNote: This screen is quantitative and backward-looking. Positions in EGX stocks carry meaningful "
        f"liquidity risk given thin float and bid-ask spreads. Always conduct independent fundamental analysis, "
        f"verify financial statements with EFSA Arabic filings, and size positions appropriately given EGP/USD "
        f"currency exposure. Past performance is not indicative of future results. This memo is for informational "
        f"purposes only and does not constitute investment advice."
    )

    return f"{para1}\n\n{'─' * 60}\n\n{para2}\n\n{'─' * 60}\n\n{para3}"
