import React from 'react'

function scoreColor(score) {
  if (score == null) return 'text-gray-400'
  if (score >= 65) return 'text-emerald-600'
  if (score >= 50) return 'text-amber-600'
  return 'text-gray-600'
}

function scoreBg(score) {
  if (score == null) return 'bg-gray-50'
  if (score >= 65) return 'bg-emerald-50 border-emerald-200'
  if (score >= 50) return 'bg-amber-50 border-amber-200'
  return 'bg-gray-50 border-gray-200'
}

export default function SectorCards({ sectors }) {
  if (!sectors || sectors.length === 0) return null

  return (
    <section className="max-w-screen-2xl mx-auto px-4 py-4">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
        Sector Summary
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
        {sectors.map((s) => (
          <div
            key={s.sector}
            className={`rounded-lg border p-3 ${scoreBg(s.median_composite)}`}
          >
            <div className="text-xs font-semibold text-gray-700 mb-2 truncate" title={s.sector}>
              {s.sector}
            </div>
            <div className="space-y-1">
              <StatRow label="Stocks" value={s.count} />
              <StatRow
                label="Med P/E"
                value={s.median_pe != null ? `${s.median_pe.toFixed(1)}x` : '—'}
              />
              <StatRow
                label="Med ROE"
                value={s.median_roe != null ? `${s.median_roe.toFixed(1)}%` : '—'}
              />
              <div className="flex justify-between items-center pt-1 border-t border-gray-200 mt-1">
                <span className="text-xs text-gray-500">Score</span>
                <span className={`text-sm font-bold tabular-nums ${scoreColor(s.median_composite)}`}>
                  {s.median_composite != null ? s.median_composite.toFixed(0) : '—'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

function StatRow({ label, value }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-xs text-gray-500">{label}</span>
      <span className="text-xs font-medium tabular-nums text-gray-800">{value}</span>
    </div>
  )
}
