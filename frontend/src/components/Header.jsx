import React from 'react'

export default function Header({ meta, loading }) {
  const lastUpdated = meta?.last_updated
    ? new Date(meta.last_updated).toLocaleString('en-US', {
        dateStyle: 'medium',
        timeStyle: 'short',
        timeZone: 'Africa/Cairo',
      }) + ' CLT'
    : null

  return (
    <header style={{ backgroundColor: '#1B3A5C' }} className="text-white shadow-lg">
      <div className="max-w-screen-2xl mx-auto px-4 py-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          {/* Title block */}
          <div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-blue-400 bg-opacity-30 flex items-center justify-center text-sm font-bold">
                EG
              </div>
              <h1 className="text-xl font-bold tracking-tight">EGX Upside Screener</h1>
            </div>
            <p className="text-blue-200 text-sm mt-0.5 ml-11">
              Quantitative screening of Egyptian Exchange stocks
            </p>
          </div>

          {/* Meta stats */}
          <div className="flex flex-wrap gap-4 text-sm">
            {loading && !meta && (
              <span className="text-blue-300 animate-pulse">Loading data…</span>
            )}
            {meta && (
              <>
                <MetaStat
                  label="Universe"
                  value={meta.universe_size ? `${meta.universe_size} stocks` : '—'}
                />
                <MetaStat
                  label="USD/EGP"
                  value={meta.usd_egp_rate ? meta.usd_egp_rate.toFixed(2) : '—'}
                />
                {meta.egx30_level && (
                  <MetaStat
                    label="EGX30"
                    value={meta.egx30_level.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                  />
                )}
                {lastUpdated && (
                  <MetaStat label="Updated" value={lastUpdated} />
                )}
                {meta.data_source && (
                  <MetaStat
                    label="Data"
                    value={meta.data_source === 'live' ? '🟢 Live' : '🟡 Static (Mar 2026)'}
                  />
                )}
                <a
                  href="/api/screener/csv"
                  className="flex items-center gap-1.5 bg-blue-500 hover:bg-blue-400 text-white px-3 py-1.5 rounded text-xs font-medium transition-colors"
                  download
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  CSV
                </a>
              </>
            )}
          </div>
        </div>

        {/* Risk disclaimer banner */}
        <div className="mt-3 text-xs text-blue-200 bg-blue-900 bg-opacity-40 rounded px-3 py-1.5 border border-blue-700 border-opacity-50">
          ⚠ EGX Risk Factors: FX exposure (EGP/USD) · Thin floats (&lt;20% on many names) · Related-party risk · Data lag vs EFSA Arabic filings · Not investment advice
        </div>
      </div>
    </header>
  )
}

function MetaStat({ label, value }) {
  return (
    <div className="flex flex-col">
      <span className="text-blue-300 text-xs uppercase tracking-wider">{label}</span>
      <span className="font-medium tabular-nums">{value}</span>
    </div>
  )
}
