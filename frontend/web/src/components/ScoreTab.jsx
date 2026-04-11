import { useState } from 'react'
import { BarChart3, Loader2, RefreshCw, Award, AlertTriangle, CheckCircle, Target, Zap, BookOpen, Network } from 'lucide-react'
import axios from 'axios'

export default function ScoreTab({ apiUrl }) {
  const [sessionId, setSessionId] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const getScore = async () => {
    if (!sessionId) return
    
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.get(`${apiUrl}/score/${sessionId}`)
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const getCategoryColor = (category) => {
    switch (category) {
      case 'excellent': return 'text-green-600 bg-green-50'
      case 'good': return 'text-blue-600 bg-blue-50'
      case 'fair': return 'text-yellow-600 bg-yellow-50'
      case 'poor': return 'text-orange-600 bg-orange-50'
      case 'critical': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-blue-600'
    if (score >= 40) return 'text-yellow-600'
    if (score >= 20) return 'text-orange-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <BarChart3 size={20} className="text-primary-600" />
          Code Archaeologist Score
        </h2>
        <p className="text-gray-600 mb-4">
          Get a comprehensive maintainability score for your codebase. 
          Based on complexity, coupling, cohesion, and documentation coverage.
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
              placeholder="Enter session ID from upload or batch analysis..."
              className="input"
            />
          </div>

          <button
            onClick={getScore}
            disabled={!sessionId || loading}
            className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? <Loader2 size={20} className="animate-spin" /> : <RefreshCw size={20} />}
            {loading ? 'Calculating...' : 'Calculate Score'}
          </button>

          {error && (
            <div className="p-4 bg-red-50 text-red-700 rounded-md flex items-center gap-2">
              <AlertTriangle size={20} />
              {error}
            </div>
          )}
        </div>
      </div>

      {result && (
        <div className="space-y-6">
          {/* Overall Score */}
          <div className="card text-center">
            <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${getCategoryColor(result.category)} mb-4`}>
              <Award size={20} />
              <span className="font-medium capitalize">{result.category}</span>
            </div>
            
            <div className="relative inline-block">
              <svg className="w-32 h-32 transform -rotate-90">
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="#e5e7eb"
                  strokeWidth="12"
                  fill="none"
                />
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke={result.overall_score >= 60 ? '#10b981' : result.overall_score >= 40 ? '#f59e0b' : '#ef4444'}
                  strokeWidth="12"
                  fill="none"
                  strokeDasharray={`${(result.overall_score / 100) * 351} 351`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className={`text-3xl font-bold ${getScoreColor(result.overall_score)}`}>
                  {result.overall_score?.toFixed(1)}
                </span>
              </div>
            </div>
            <p className="text-gray-500 mt-2">out of 100</p>
          </div>

          {/* Component Scores */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card text-center">
              <Target size={24} className="mx-auto text-purple-600 mb-2" />
              <p className="text-2xl font-bold text-gray-900">
                {result.component_scores?.complexity}
              </p>
              <p className="text-xs text-gray-600">Complexity</p>
            </div>
            <div className="card text-center">
              <Network size={24} className="mx-auto text-blue-600 mb-2" />
              <p className="text-2xl font-bold text-gray-900">
                {result.component_scores?.coupling}
              </p>
              <p className="text-xs text-gray-600">Coupling</p>
            </div>
            <div className="card text-center">
              <Zap size={24} className="mx-auto text-yellow-600 mb-2" />
              <p className="text-2xl font-bold text-gray-900">
                {result.component_scores?.cohesion}
              </p>
              <p className="text-xs text-gray-600">Cohesion</p>
            </div>
            <div className="card text-center">
              <BookOpen size={24} className="mx-auto text-green-600 mb-2" />
              <p className="text-2xl font-bold text-gray-900">
                {result.component_scores?.documentation}
              </p>
              <p className="text-xs text-gray-600">Documentation</p>
            </div>
          </div>

          {/* Detailed Metrics */}
          {result.metrics && (
            <div className="card">
              <h3 className="font-semibold mb-4">Detailed Metrics</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex justify-between py-2 border-b">
                  <span className="text-gray-600">Graph Density</span>
                  <span className="font-mono">{result.metrics.graph_density?.toFixed(3)}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-gray-600">Avg Fan-Out</span>
                  <span className="font-mono">{result.metrics.avg_fan_out?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-gray-600">Max Fan-Out</span>
                  <span className="font-mono">{result.metrics.max_fan_out}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-gray-600">Dead Code %</span>
                  <span className={`font-mono ${result.metrics.dead_code_pct > 10 ? 'text-red-600' : 'text-green-600'}`}>
                    {result.metrics.dead_code_pct?.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-gray-600">Cyclomatic Proxy</span>
                  <span className="font-mono">{result.metrics.cyclomatic_proxy}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-gray-600">Causal Complexity</span>
                  <span className="font-mono">{result.metrics.causal_complexity?.toFixed(2)}</span>
                </div>
              </div>
            </div>
          )}

          {/* Issues & Strengths */}
          <div className="grid md:grid-cols-2 gap-6">
            {result.top_issues && result.top_issues.length > 0 && (
              <div className="card border-l-4 border-red-500">
                <h3 className="font-semibold text-red-900 mb-3 flex items-center gap-2">
                  <AlertTriangle size={18} />
                  Top Issues
                </h3>
                <ul className="space-y-2">
                  {result.top_issues.map((issue, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-red-800">
                      <span className="text-red-500 mt-0.5">•</span>
                      {issue}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.strengths && result.strengths.length > 0 && (
              <div className="card border-l-4 border-green-500">
                <h3 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
                  <CheckCircle size={18} />
                  Strengths
                </h3>
                <ul className="space-y-2">
                  {result.strengths.map((strength, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-green-800">
                      <span className="text-green-500 mt-0.5">✓</span>
                      {strength}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
