import { useState } from 'react'
import { PlayCircle, AlertTriangle, Loader2, GitBranch, AlertCircle, CheckCircle2 } from 'lucide-react'
import axios from 'axios'

export default function WhatIfTab({ apiUrl }) {
  const [sessionId, setSessionId] = useState('')
  const [functionName, setFunctionName] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const simulateRemoval = async () => {
    if (!sessionId || !functionName) return
    
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(
        `${apiUrl}/whatif/simulate?session_id=${sessionId}&remove_function=${functionName}`
      )
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50'
      case 'high': return 'text-orange-600 bg-orange-50'
      case 'medium': return 'text-yellow-600 bg-yellow-50'
      case 'low': return 'text-green-600 bg-green-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Play size={20} className="text-primary-600" />
          What-If Simulator
        </h2>
        <p className="text-gray-600 mb-4">
          Simulate removing a function and see the cascading effects. Identify critical paths 
          and alternative routes before refactoring.
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Session ID
            </label>
            <input
              type="text"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              placeholder="Enter session ID..."
              className="input"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Function to Remove
            </label>
            <input
              type="text"
              value={functionName}
              onChange={(e) => setFunctionName(e.target.value)}
              placeholder="e.g., process_data, helper_function"
              className="input"
            />
          </div>

          <button
            onClick={simulateRemoval}
            disabled={!sessionId || !functionName || loading}
            className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? <Loader2 size={20} className="animate-spin" /> : <Play size={20} />}
            {loading ? 'Simulating...' : 'Run Simulation'}
          </button>

          {error && (
            <div className="p-4 bg-red-50 text-red-700 rounded-md flex items-center gap-2">
              <AlertCircle size={20} />
              {error}
            </div>
          )}
        </div>
      </div>

      {result && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className={`p-4 rounded-lg ${getSeverityColor(result.summary?.max_severity)}`}>
              <p className="text-2xl font-bold">
                {result.summary?.affected_count || 0}
              </p>
              <p className="text-sm">Functions Affected</p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg text-blue-800">
              <p className="text-2xl font-bold">
                {result.summary?.cascade_depth || 0}
              </p>
              <p className="text-sm">Cascade Depth</p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg text-purple-800">
              <p className="text-2xl font-bold">
                {((result.summary?.total_break_probability || 0) * 100).toFixed(0)}%
              </p>
              <p className="text-sm">Break Probability</p>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg text-orange-800">
              <p className="text-2xl font-bold">
                {result.alternative_paths?.length || 0}
              </p>
              <p className="text-sm">Alternative Paths</p>
            </div>
          </div>

          {/* Removed Function */}
          <div className="card bg-red-50 border-red-200">
            <div className="flex items-center gap-3">
              <AlertTriangle className="text-red-600" size={24} />
              <div>
                <p className="font-medium text-red-900">Removing Function</p>
                <p className="text-2xl font-bold text-red-700 font-mono">{result.removed_function}</p>
              </div>
            </div>
          </div>

          {/* Critical Path */}
          {result.critical_path && result.critical_path.length > 0 && (
            <div className="card">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <GitBranch size={18} />
                Critical Path (Highest Risk)
              </h3>
              <div className="flex items-center gap-2 flex-wrap">
                {result.critical_path.map((func, idx) => (
                  <span key={idx} className="flex items-center gap-2">
                    <span className="px-3 py-1 bg-red-100 text-red-700 rounded font-mono text-sm">
                      {func}
                    </span>
                    {idx < result.critical_path.length - 1 && (
                      <span className="text-gray-400">→</span>
                    )}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Affected Functions */}
          {result.affected_functions && result.affected_functions.length > 0 && (
            <div className="card">
              <h3 className="font-semibold mb-3">Affected Functions</h3>
              <div className="space-y-2">
                {result.affected_functions
                  .sort((a, b) => b.break_probability - a.break_probability)
                  .map((func, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-md ${getSeverityColor(func.severity)}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {func.severity === 'critical' || func.severity === 'high' ? (
                          <AlertTriangle size={16} />
                        ) : (
                          <CheckCircle2 size={16} />
                        )}
                        <span className="font-mono font-medium">{func.function}</span>
                      </div>
                      <span className="text-sm font-bold">
                        {(func.break_probability * 100).toFixed(0)}% break risk
                      </span>
                    </div>
                    {func.reason && (
                      <p className="text-sm mt-1 opacity-80">{func.reason}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations && result.recommendations.length > 0 && (
            <div className="card bg-green-50 border-green-200">
              <h3 className="font-semibold mb-3 text-green-900 flex items-center gap-2">
                <CheckCircle2 size={18} />
                Recommendations
              </h3>
              <ul className="space-y-2">
                {result.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-green-800">
                    <span className="text-green-600 mt-0.5">•</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
