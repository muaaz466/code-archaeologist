import { useState, useEffect } from 'react'
import { GitGraph, ZoomIn, ZoomOut, Move, Info, AlertCircle } from 'lucide-react'

export default function GraphViewPage({ apiUrl, sessionId, analysisData }) {
  const [graphData, setGraphData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [zoom, setZoom] = useState(1)

  useEffect(() => {
    if (sessionId) {
      fetchGraphData()
    }
  }, [sessionId])

  const fetchGraphData = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${apiUrl}/query/${sessionId}?query_type=metrics`)
      const data = await response.json()
      if (response.ok) {
        setGraphData(data)
      } else {
        setError(data.detail || 'Failed to fetch graph')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (!sessionId) {
    return (
      <div className="card text-center py-12">
        <GitGraph size={48} className="mx-auto text-[#64748b] mb-4" />
        <h3 className="text-xl font-semibold mb-2">No Active Session</h3>
        <p className="text-[#94a3b8] mb-4">
          Upload a file on the Dashboard to view the causal graph
        </p>
        <a href="/" className="btn btn-primary">
          Go to Dashboard
        </a>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Graph View</h2>
          <p className="text-[#94a3b8]">Interactive causal dependency graph</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setZoom(z => Math.min(z + 0.2, 2))}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10"
          >
            <ZoomIn size={20} />
          </button>
          <span className="text-sm text-[#94a3b8] min-w-[60px] text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoom(z => Math.max(z - 0.2, 0.5))}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10"
          >
            <ZoomOut size={20} />
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#6366f1]"></div>
        </div>
      )}

      {error && (
        <div className="card flex items-center gap-2 text-red-400">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {/* Graph Visualization Placeholder */}
      <div className="card relative min-h-[500px]">
        <div 
          className="absolute inset-0 flex items-center justify-center"
          style={{ transform: `scale(${zoom})` }}
        >
          {analysisData?.functions?.length > 0 ? (
            <div className="grid grid-cols-3 gap-8">
              {analysisData.functions.slice(0, 9).map((func, i) => (
                <button
                  key={i}
                  onClick={() => setSelectedNode(func)}
                  className={`p-4 rounded-xl border transition-all ${
                    selectedNode === func
                      ? 'border-[#6366f1] bg-[#6366f1]/20'
                      : 'border-white/10 bg-white/5 hover:bg-white/10'
                  }`}
                >
                  <div className="text-sm font-medium">{func}</div>
                  <div className="text-xs text-[#64748b] mt-1">
                    {analysisData.language || 'unknown'}
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-center text-[#64748b]">
              <GitGraph size={64} className="mx-auto mb-4 opacity-50" />
              <p>Graph visualization requires analysis data</p>
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 card p-3 space-y-2">
          <div className="flex items-center gap-2 text-xs">
            <div className="w-3 h-3 rounded-full bg-[#6366f1]"></div>
            <span>Function Node</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <div className="w-3 h-3 rounded-full bg-[#ec4899]"></div>
            <span>High Risk</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <div className="w-3 h-3 rounded-full bg-[#10b981]"></div>
            <span>Data Flow</span>
          </div>
        </div>
      </div>

      {/* Node Details */}
      {selectedNode && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold flex items-center gap-2">
              <Info size={18} />
              Function Details
            </h3>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-[#64748b] hover:text-white"
            >
              ✕
            </button>
          </div>
          <div className="space-y-3">
            <div>
              <span className="text-sm text-[#94a3b8]">Name:</span>
              <span className="ml-2 font-mono">{selectedNode}</span>
            </div>
            <div>
              <span className="text-sm text-[#94a3b8]">Language:</span>
              <span className="ml-2">{analysisData?.language || 'unknown'}</span>
            </div>
            <div className="flex gap-2 mt-4">
              <a href="/whatif" className="btn btn-primary text-sm">
                Simulate Removal
              </a>
              <button className="btn btn-secondary text-sm">
                View Callers
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
