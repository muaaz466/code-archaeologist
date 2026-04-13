import { useState } from 'react'
import { PlayCircle, AlertTriangle, ArrowRight, CheckCircle, XCircle } from 'lucide-react'

export default function WhatIfPage({ apiUrl, sessionId, analysisData }) {
  const [selectedFunction, setSelectedFunction] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const runSimulation = async () => {
    if (!selectedFunction || !sessionId) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${apiUrl}/whatif/${sessionId}?function=${encodeURIComponent(selectedFunction)}`, {
        method: 'POST',
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Simulation failed')
      }

      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (!sessionId) {
    return (
      <div className="card text-center py-12">
        <AlertTriangle size={48} className="mx-auto text-[#64748b] mb-4" />
        <h3 className="text-xl font-semibold mb-2">No Active Session</h3>
        <p className="text-[#94a3b8] mb-4">
          Upload a file first to run what-if simulations
        </p>
        <a href="/" className="btn btn-primary">
          Go to Dashboard
        </a>
      </div>
    )
  }

  const functions = analysisData?.functions || []

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold">What-If Simulator</h2>
        <p className="text-[#94a3b8]">Simulate removing a function and see the impact</p>
      </div>

      {/* Input Section */}
      <div className="card">
        <label className="block text-sm font-medium mb-2">
          Select function to remove:
        </label>
        
        {functions.length > 0 ? (
          <select
            value={selectedFunction}
            onChange={(e) => setSelectedFunction(e.target.value)}
            className="w-full p-3 rounded-lg bg-[#0f172a] border border-white/10 text-white mb-4"
          >
            <option value="">Choose a function...</option>
            {functions.map((func, i) => (
              <option key={i} value={func}>{func}</option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            value={selectedFunction}
            onChange={(e) => setSelectedFunction(e.target.value)}
            placeholder="Enter function name..."
            className="w-full p-3 rounded-lg bg-[#0f172a] border border-white/10 text-white mb-4"
          />
        )}

        <button
          onClick={runSimulation}
          disabled={!selectedFunction || loading}
          className="btn btn-primary w-full"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
              Running Simulation...
            </>
          ) : (
            <>
              <PlayCircle size={18} />
              Run Simulation
            </>
          )}
        </button>

        {error && (
          <div className="flex items-center gap-2 mt-4 text-red-400 bg-red-500/10 p-3 rounded-lg">
            <XCircle size={18} />
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card text-center">
              <div className="text-3xl font-bold text-[#ec4899]">
                {result.summary?.affected_count || 0}
              </div>
              <div className="text-sm text-[#94a3b8] mt-1">Functions Affected</div>
            </div>
            <div className="card text-center">
              <div className="text-3xl font-bold text-[#8b5cf6]">
                {result.summary?.cascade_depth || 0}
              </div>
              <div className="text-sm text-[#94a3b8] mt-1">Cascade Depth</div>
            </div>
            <div className="card text-center">
              <div className="text-3xl font-bold text-[#f59e0b]">
                {Math.round((result.summary?.total_break_probability || 0) * 100)}%
              </div>
              <div className="text-sm text-[#94a3b8] mt-1">Break Probability</div>
            </div>
          </div>

          {/* Critical Path */}
          {result.critical_path?.length > 0 && (
            <div className="card">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <AlertTriangle size={18} className="text-[#ec4899]" />
                Critical Path
              </h3>
              <div className="flex flex-wrap items-center gap-2">
                {result.critical_path.map((node, i) => (
                  <span key={i} className="flex items-center gap-2">
                    <span className="px-3 py-1 rounded-lg bg-[#ec4899]/20 text-[#ec4899] text-sm">
                      {node}
                    </span>
                    {i < result.critical_path.length - 1 && (
                      <ArrowRight size={14} className="text-[#64748b]" />
                    )}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Affected Functions */}
          {result.affected_functions?.length > 0 && (
            <div className="card">
              <h3 className="font-semibold mb-3">Affected Functions</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {result.affected_functions.map((func, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 p-2 rounded-lg bg-white/5"
                  >
                    <AlertTriangle size={14} className="text-[#f59e0b]" />
                    <span className="text-sm">{func.name || func}</span>
                    {func.break_probability && (
                      <span className="text-xs text-[#f59e0b] ml-auto">
                        {Math.round(func.break_probability * 100)}% risk
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Alternative Paths */}
          {result.alternative_paths?.length > 0 && (
            <div className="card">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <CheckCircle size={18} className="text-[#10b981]" />
                Alternative Paths
              </h3>
              <p className="text-sm text-[#94a3b8] mb-2">
                {result.alternative_paths.length} alternative execution paths found
              </p>
            </div>
          )}

          {/* Warning */}
          {result.warning && (
            <div className="card bg-[#f59e0b]/10 border-[#f59e0b]/30">
              <p className="text-[#f59e0b] flex items-center gap-2">
                <AlertTriangle size={18} />
                {result.warning}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
