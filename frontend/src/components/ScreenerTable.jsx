import React, { useState, useMemo } from 'react'

const COLUMNS = [
  { key: 'rank', label: '#', width: 'w-10', align: 'text-center' },
  { key: 'ticker', label: 'Ticker', width: 'w-20' },
  { key: 'name', label: 'Company', width: 'min-w-[140px]' },
  { key: 'sector', label: 'Sector', width: 'min-w-[120px]' },
  { key: 'price_egp', label: 'Price (EGP)', width: 'w-28', align: 'text-right', numeric: true },
  { key: 'market_cap_egp_b', label: 'MCap (EGPb)', width: 'w-28', align: 'text-right', numeric: true },
  { key: 'market_cap_usd_m', label: 'MCap (USD m)', width: 'w-28', align: 'text-right', numeric: true },
  { key: 'pe', label: 'P/E', width: 'w-20', align: 'text-right', numeric: true },
  { key: 'ev_ebitda', label: 'EV/EBITDA', width: 'w-24', align: 'text-right', numeric: true },
  { key: 'pb', label: 'P/B', width: 'w-20', align: 'text-right', numeric: true },
  { key: 'revenue_growth_pct', label: 'Rev Grw %', width: 'w-24', align: 'text-right', numeric: true },
  { key: 'roe_pct', label: 'ROE %', width: 'w-20', align: 'text-right', numeric: true },
  { key: 'debt_equity', label: 'D/E', width: 'w-20', align: 'text-right', numeric: true },
  { key: 'current_ratio', label: 'Curr Ratio', width: 'w-24', align: 'text-right', numeric: true },
  { key: 'return_52w_pct', label: '52W Ret %', width: 'w-24', align: 'text-right', numeric: true },
  { key: 'composite_score', label: 'Score', width: 'w-20', align: 'text-right', numeric: true },
]

function fmt(val, key) {
  if (val == null) return <span className="text-gray-300">—</span>
  if (key === 'pe' || key === 'ev_ebitda') return `${val.toFixed(1)}x`
  if (key === 'pb') return `${val.toFixed(2)}x`
  if (key === 'price_egp') return val.toFixed(2)
  if (key === 'market_cap_egp_b') return val.toFixed(2)
  if (key === 'market_cap_usd_m') return val.toFixed(0)
  if (key === 'revenue_growth_pct' || key === 'roe_pct' || key === 'return_52w_pct') {
    return `${val > 0 ? '+' : ''}${val.toFixed(1)}%`
  }
  if (key === 'debt_equity') return val.toFixed(2)
  if (key === 'current_ratio') return val.toFixed(2)
  if (key === 'composite_score') return val.toFixed(1)
  return val
}

function scoreClass(score) {
  if (score == null) return ''
  if (score >= 65) return 'text-emerald-700 font-semibold'
  if (score >= 50) return 'text-amber-700 font-semibold'
  return 'text-gray-600'
}

function scoreBadgeBg(score) {
  if (score == null) return 'bg-gray-100 text-gray-500'
  if (score >= 65) return 'bg-emerald-100 text-emerald-800'
  if (score >= 50) return 'bg-amber-100 text-amber-800'
  return 'bg-gray-100 text-gray-600'
}

function cellClass(key, val) {
  if (key === 'current_ratio' && val != null && val < 1.0) return 'bg-red-50 text-red-700'
  if (key === 'debt_equity' && val != null && val > 2.0) return 'bg-red-50 text-red-700'
  if (key === 'pb' && val != null && val < 1.0) return 'bg-emerald-50 text-emerald-700'
  return ''
}

function FlagBadge({ flag }) {
  const map = {
    deep_value: { label: 'Deep Value', cls: 'bg-emerald-100 text-emerald-700' },
    overleveraged: { label: 'Overleveraged', cls: 'bg-red-100 text-red-700' },
    liquidity_risk: { label: 'Liq Risk', cls: 'bg-orange-100 text-orange-700' },
  }
  const info = map[flag] || { label: flag, cls: 'bg-gray-100 text-gray-600' }
  return (
    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${info.cls}`}>
      {info.label}
    </span>
  )
}

function ScoreBar({ label, value, color }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 w-20">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${Math.min(value || 0, 100)}%` }}
        />
      </div>
      <span className="text-xs tabular-nums text-gray-600 w-8 text-right">
        {value != null ? value.toFixed(0) : '—'}
      </span>
    </div>
  )
}

export default function ScreenerTable({ stocks, sectors }) {
  const [sortKey, setSortKey] = useState('composite_score')
  const [sortDir, setSortDir] = useState('desc')
  const [expandedRow, setExpandedRow] = useState(null)
  const [sectorFilter, setSectorFilter] = useState('all')
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    let data = stocks || []
    if (sectorFilter !== 'all') {
      data = data.filter((s) => s.sector === sectorFilter)
    }
    if (search.trim()) {
      const q = search.trim().toLowerCase()
      data = data.filter(
        (s) =>
          s.ticker.toLowerCase().includes(q) ||
          (s.name || '').toLowerCase().includes(q)
      )
    }
    return [...data].sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      if (typeof av === 'string') return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
      return sortDir === 'asc' ? av - bv : bv - av
    })
  }, [stocks, sortKey, sortDir, sectorFilter, search])

  function handleSort(key) {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  function SortIcon({ col }) {
    if (sortKey !== col) return <span className="text-gray-300 ml-0.5">↕</span>
    return <span className="text-blue-500 ml-0.5">{sortDir === 'asc' ? '↑' : '↓'}</span>
  }

  const sectorList = useMemo(() => {
    const s = new Set((stocks || []).map((x) => x.sector))
    return ['all', ...Array.from(s).sort()]
  }, [stocks])

  return (
    <section className="max-w-screen-2xl mx-auto px-4 pb-4">
      {/* Controls */}
      <div className="flex flex-wrap gap-3 mb-3 items-center">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
          Screener Results ({filtered.length})
        </h2>
        <div className="flex-1" />
        <input
          type="text"
          placeholder="Search ticker / company…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="text-sm border border-gray-200 rounded px-3 py-1.5 w-52 focus:outline-none focus:ring-2 focus:ring-blue-300"
        />
        <select
          value={sectorFilter}
          onChange={(e) => setSectorFilter(e.target.value)}
          className="text-sm border border-gray-200 rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
        >
          {sectorList.map((s) => (
            <option key={s} value={s}>
              {s === 'all' ? 'All sectors' : s}
            </option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm bg-white">
        <table className="min-w-full text-sm">
          <thead>
            <tr style={{ backgroundColor: '#1B3A5C' }} className="text-white">
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className={`px-3 py-2.5 text-xs font-semibold uppercase tracking-wide cursor-pointer select-none whitespace-nowrap hover:bg-blue-800 transition-colors ${col.align || 'text-left'} ${col.width}`}
                >
                  {col.label}
                  <SortIcon col={col.key} />
                </th>
              ))}
              <th className="px-3 py-2.5 text-xs font-semibold uppercase tracking-wide w-16 text-center">
                Flags
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((stock, idx) => {
              const isExpanded = expandedRow === stock.ticker
              const rowBg = idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'
              return (
                <React.Fragment key={stock.ticker}>
                  <tr
                    className={`${rowBg} hover:bg-blue-50 cursor-pointer transition-colors border-b border-gray-100`}
                    onClick={() => setExpandedRow(isExpanded ? null : stock.ticker)}
                  >
                    {COLUMNS.map((col) => {
                      const val = stock[col.key]
                      const extraClass = cellClass(col.key, val)
                      const isScore = col.key === 'composite_score'
                      return (
                        <td
                          key={col.key}
                          className={`px-3 py-2 tabular-nums ${col.align || ''} ${extraClass}`}
                        >
                          {isScore ? (
                            <span className={`px-2 py-0.5 rounded text-xs font-bold ${scoreBadgeBg(val)}`}>
                              {val != null ? val.toFixed(1) : '—'}
                            </span>
                          ) : (
                            <span className={col.key === 'ticker' ? 'font-semibold text-blue-700' : ''}>
                              {fmt(val, col.key)}
                            </span>
                          )}
                        </td>
                      )
                    })}
                    <td className="px-3 py-2">
                      <div className="flex flex-wrap gap-1 justify-center">
                        {(stock.flags || []).map((f) => (
                          <FlagBadge key={f} flag={f} />
                        ))}
                      </div>
                    </td>
                  </tr>

                  {/* Expanded thesis row */}
                  {isExpanded && (
                    <tr className="bg-blue-50 border-b border-blue-100">
                      <td colSpan={COLUMNS.length + 1} className="px-4 py-3">
                        <div className="flex flex-col gap-2">
                          <div className="flex items-start gap-3">
                            <div className="flex-1">
                              <span className="text-xs font-semibold text-blue-700 uppercase tracking-wide">
                                Upside Thesis
                              </span>
                              <p className="text-sm text-gray-700 mt-0.5">{stock.thesis}</p>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-1">
                            <ScoreBar label="Valuation" value={stock.score_valuation} color="bg-blue-400" />
                            <ScoreBar label="Growth" value={stock.score_growth} color="bg-emerald-400" />
                            <ScoreBar label="Quality" value={stock.score_quality} color="bg-violet-400" />
                            <ScoreBar label="Momentum" value={stock.score_momentum} color="bg-amber-400" />
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              )
            })}

            {filtered.length === 0 && (
              <tr>
                <td colSpan={COLUMNS.length + 1} className="text-center py-12 text-gray-400">
                  No stocks match your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
