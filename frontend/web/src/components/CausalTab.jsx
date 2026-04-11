import { useState } from 'react'
import { GitGraph, Loader2, RefreshCw, Download, Eye } from 'lucide-react'
import axios from 'axios'

export default function CausalTab({ apiUrl }) {
  const [sessionId, setSessionId] = useState('')
  const [minConfidence, setMinConfidence] = useState(0.3)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const discoverCausal = async () => {
    if (!sessionId) return
    
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(
        `${apiUrl}/causal/discover?session_id=${sessionId}&min_confidence=${minConfidence}`
      )
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const downloadGraph = () => {
    if (!result) return
    const dataStr = JSON.stringify(result, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `causal-graph-${sessionId}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <GitGraph size={20} className="text-primary-600" />
          Causal Discovery
        </h2>
        <p className="text-gray-600 mb-4">
          Build a causal graph from trace data. Discover which functions influence others based on 
          temporal ordering and statistical dependency.
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
              placeholder="Enter session ID from upload..."
              className="input"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Minimum Confidence: {minConfidence}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={minConfidence}
              onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-gray-500 mt-1">
              Higher values = stronger causal relationships only
            </p>
          </div>

          <button
            onClick={discoverCausal}
            disabled={!sessionId || loading}
            className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? <Loader2 size={20} className="animate-spin" /> : <RefreshCw size={20} />}
            {loading ? 'Discovering...' : 'Discover Causal Graph'}
          </button>

          {error && (
            <div className="p-4 bg-red-50 text-red-700 rounded-md">
              ⚠️ {error}
            </div>
          )}
        </div>
      </div>

      {result && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Causal Graph Results</h3>
            <button
              onClick={downloadGraph}
              className="btn-secondary flex items-center gap-2 text-sm"
            >
              <Download size={16} />
              Export JSON
            </button>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-blue-600">{result.nodes?.length || 0}</p>
              <p className="text-sm text-blue-800">Nodes</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-green-600">{result.edges?.length || 0}</p>
              <p className="text-sm text-green-800">Causal Edges</p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-purple-600">
                {result.interventions?.length || 0}
              </p>
              <p className="text-sm text-purple-800">Interventions</p>
            </div>
          </div>

          {/* Edges Table */}
          {result.edges && result.edges.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left">Source</th>
                    <th className="px-4 py-2 text-left">→</th>
                    <th className="px-4 py-2 text-left">Target</th>
                    <th className="px-4 py-2 text-left">Confidence</th>
                    <th className="px-4 py-2 text-left">Strength</th>
                  </tr>
                </thead>
                <tbody>
                  {result.edges
                    .sort((a, b) => b.confidence - a.confidence)
                    .map((edge, idx) => (
                    <tr key={idx} className="border-t">
                      <td className="px-4 py-2 font-mono">{edge.source}</td>
                      <td className="px-4 py-2 text-gray-400">→</td>
                      <td className="px-4 py-2 font-mono">{edge.target}</td>
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-primary-600 h-2 rounded-full"
                              style={{ width: `${edge.confidence * 100}%` }}
                            />
                          </div>
                          <span className="text-xs">{(edge.confidence * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-2 text-gray-600">
                        {edge.strength?.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Nodes List */}
          {result.nodes && result.nodes.length > 0 && (
            <div className="mt-6">
              <h4 className="font-medium mb-2">Functions (Nodes)</h4>
              <div className="flex flex-wrap gap-2">
                {result.nodes.map(node => (
                  <span
                    key={node}
                    className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-mono"
                  >
                    {node}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
