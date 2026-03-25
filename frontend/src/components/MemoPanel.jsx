import React, { useState, useEffect } from 'react'

export default function MemoPanel() {
  const [open, setOpen] = useState(false)
  const [memo, setMemo] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (open && !memo && !loading) {
      setLoading(true)
      fetch('/api/screener/memo')
        .then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`)
          return r.text()
        })
        .then((text) => {
          setMemo(text)
          setLoading(false)
        })
        .catch((err) => {
          setError(err.message)
          setLoading(false)
        })
    }
  }, [open])

  return (
    <section className="max-w-screen-2xl mx-auto px-4 pb-6">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 text-sm font-semibold text-gray-600 hover:text-gray-900 transition-colors group"
      >
        <span
          className={`inline-block transition-transform duration-200 ${open ? 'rotate-90' : ''}`}
        >
          ▶
        </span>
        Investment Memo
        <span className="text-xs font-normal text-gray-400 group-hover:text-gray-500">
          (3-paragraph analysis)
        </span>
      </button>

      {open && (
        <div className="mt-3 bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          <div
            className="px-4 py-2 text-xs font-semibold text-white uppercase tracking-wider"
            style={{ backgroundColor: '#1B3A5C' }}
          >
            EGX Investment Memo
          </div>
          <div className="p-6">
            {loading && (
              <div className="flex items-center gap-2 text-gray-500 text-sm">
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Generating memo…
              </div>
            )}
            {error && (
              <div className="text-red-600 text-sm">Error loading memo: {error}</div>
            )}
            {memo && (
              <pre className="whitespace-pre-wrap font-mono text-xs text-gray-700 leading-relaxed">
                {memo}
              </pre>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
