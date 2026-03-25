import React, { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import ScreenerTable from './components/ScreenerTable'
import SectorCards from './components/SectorCards'
import MemoPanel from './components/MemoPanel'

function Spinner() {
  return (
    <div className="flex flex-col items-center justify-center py-24 gap-4">
      <svg className="animate-spin w-10 h-10 text-blue-400" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <div className="text-center">
        <p className="text-gray-600 font-medium">Loading EGX data…</p>
        <p className="text-gray-400 text-sm mt-1">
          Fetching live prices from Yahoo Finance. This may take up to 60 seconds on first load.
        </p>
      </div>
    </div>
  )
}

function ErrorPanel({ error, onRetry }) {
  return (
    <div className="max-w-lg mx-auto mt-16 p-6 bg-red-50 border border-red-200 rounded-lg text-center">
      <div className="text-red-500 text-3xl mb-3">⚠</div>
      <h3 className="font-semibold text-red-700 mb-1">Data Unavailable</h3>
      <p className="text-sm text-red-600 mb-4">{error}</p>
      <button
        onClick={onRetry}
        className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors"
      >
        Retry
      </button>
    </div>
  )
}

function DataLoadingBanner() {
  return (
    <div className="max-w-screen-2xl mx-auto px-4 py-3">
      <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 flex items-center gap-3 text-sm text-blue-700">
        <svg className="animate-spin w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        Data pipeline is initializing — fetching live prices for 53 EGX tickers. Refresh in 60–90 seconds.
      </div>
    </div>
  )
}

const POLL_INTERVAL_MS = 8000

export default function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [initializing, setInitializing] = useState(false)
  const [error, setError] = useState(null)

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch('/api/screener')
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `HTTP ${res.status}`)
      }
      const json = await res.json()
      if (json.universe_size === 0) {
        // Backend still initializing
        setInitializing(true)
        return false
      }
      setData(json)
      setInitializing(false)
      setError(null)
      return true
    } catch (err) {
      setError(err.message)
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  // Initial load + polling while initializing
  useEffect(() => {
    let timer
    async function load() {
      const success = await fetchData()
      if (!success && !error) {
        timer = setTimeout(load, POLL_INTERVAL_MS)
      }
    }
    load()
    return () => clearTimeout(timer)
  }, [fetchData])

  // Poll while initializing
  useEffect(() => {
    if (!initializing) return
    const timer = setInterval(async () => {
      const success = await fetchData()
      if (success) clearInterval(timer)
    }, POLL_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [initializing, fetchData])

  return (
    <div className="min-h-screen bg-gray-50">
      <Header meta={data} loading={loading} />

      <main>
        {loading && <Spinner />}

        {!loading && error && (
          <ErrorPanel error={error} onRetry={() => { setLoading(true); fetchData() }} />
        )}

        {!loading && !error && (
          <>
            {initializing && <DataLoadingBanner />}

            {data && (
              <>
                <div className="py-4" />
                <SectorCards sectors={data.sector_summary} />
                <div className="py-2" />
                <ScreenerTable stocks={data.stocks} sectors={data.sector_summary} />
                <div className="py-4" />
                <MemoPanel />
              </>
            )}
          </>
        )}
      </main>

      <footer className="border-t border-gray-200 py-4 mt-8">
        <div className="max-w-screen-2xl mx-auto px-4 text-xs text-gray-400 text-center">
          EGX Upside Screener — Quantitative scores only, not investment advice · Prices in EGP ·{' '}
          {data?.data_source !== 'live'
            ? 'Data source: stockanalysis.com (Mar 2026). Live data temporarily unavailable due to Yahoo Finance rate limits.'
            : 'Data via Yahoo Finance (yfinance) · EGX data may lag 1–2 quarters vs EFSA Arabic filings'}
        </div>
      </footer>
    </div>
  )
}
