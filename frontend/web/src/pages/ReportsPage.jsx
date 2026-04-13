import { useState } from 'react'
import { FileText, Download, FileCode, CheckCircle, AlertCircle } from 'lucide-react'

export default function ReportsPage({ apiUrl, sessionId: propSessionId, analysisData }) {
  // Fallback to localStorage if prop is null (page refresh/direct navigation)
  const sessionId = propSessionId || localStorage.getItem('codearch_session_id')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const exportPDF = async () => {
    if (!sessionId) return

    setLoading(true)
    setError(null)
    setSuccess(false)

    try {
      const response = await fetch(`${apiUrl}/export/pdf?session_id=${sessionId}`, {
        method: 'GET',
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Export failed')
      }

      // Download the PDF
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `code-archaeologist-report-${sessionId}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      setSuccess(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (!sessionId) {
    return (
      <div className="card text-center py-12">
        <FileText size={48} className="mx-auto text-[#64748b] mb-4" />
        <h3 className="text-xl font-semibold mb-2">No Active Session</h3>
        <p className="text-[#94a3b8] mb-4">
          Analyze a project first to generate reports
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
      <div>
        <h2 className="text-2xl font-bold">Reports & Exports</h2>
        <p className="text-[#94a3b8]">Export analysis results and view full reports</p>
      </div>

      {/* Export Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* PDF Export */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-xl bg-[#ec4899]/10 text-[#ec4899]">
              <FileText size={24} />
            </div>
            <div>
              <h3 className="font-semibold">PDF Report</h3>
              <p className="text-sm text-[#94a3b8]">Full analysis with graphs</p>
            </div>
          </div>
          
          <button
            onClick={exportPDF}
            disabled={loading}
            className="btn btn-primary w-full"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                Generating...
              </>
            ) : (
              <>
                <Download size={18} />
                Download PDF
              </>
            )}
          </button>

          {success && (
            <div className="flex items-center gap-2 mt-3 text-green-400 text-sm">
              <CheckCircle size={16} />
              PDF downloaded successfully
            </div>
          )}
        </div>

        {/* JSON Export */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-xl bg-[#6366f1]/10 text-[#6366f1]">
              <FileCode size={24} />
            </div>
            <div>
              <h3 className="font-semibold">JSON Data</h3>
              <p className="text-sm text-[#94a3b8]">Raw analysis data</p>
            </div>
          </div>
          
          <button
            onClick={() => {
              const dataStr = JSON.stringify(analysisData, null, 2)
              const blob = new Blob([dataStr], { type: 'application/json' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `analysis-${sessionId}.json`
              a.click()
              URL.revokeObjectURL(url)
            }}
            className="btn btn-secondary w-full"
          >
            <Download size={18} />
            Download JSON
          </button>
        </div>
      </div>

      {/* Analysis Summary */}
      {analysisData && (
        <div className="card">
          <h3 className="font-semibold mb-4">Analysis Summary</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="p-3 rounded-lg bg-white/5 text-center">
              <div className="text-2xl font-bold text-[#6366f1]">
                {analysisData.functions?.length || analysisData.nodes || 0}
              </div>
              <div className="text-xs text-[#94a3b8]">Functions</div>
            </div>
            <div className="p-3 rounded-lg bg-white/5 text-center">
              <div className="text-2xl font-bold text-[#8b5cf6]">
                {analysisData.total_events || analysisData.edges || 0}
              </div>
              <div className="text-xs text-[#94a3b8]">Events</div>
            </div>
            <div className="p-3 rounded-lg bg-white/5 text-center">
              <div className="text-2xl font-bold text-[#ec4899]">
                {Array.isArray(analysisData.languages) 
                  ? analysisData.languages.length 
                  : 1}
              </div>
              <div className="text-xs text-[#94a3b8]">Languages</div>
            </div>
            <div className="p-3 rounded-lg bg-white/5 text-center">
              <div className="text-2xl font-bold text-[#10b981]">
                {analysisData.files_analyzed || 1}
              </div>
              <div className="text-xs text-[#94a3b8]">Files</div>
            </div>
          </div>

          {/* Languages */}
          {analysisData.languages && (
            <div className="mb-4">
              <h4 className="text-sm text-[#94a3b8] mb-2">Languages Detected</h4>
              <div className="flex flex-wrap gap-2">
                {(Array.isArray(analysisData.languages) 
                  ? analysisData.languages 
                  : [analysisData.languages]
                ).map((lang, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 rounded-full text-xs bg-[#6366f1]/20 text-[#6366f1]"
                  >
                    {lang}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* File Stats for batch */}
          {analysisData.file_stats && Object.keys(analysisData.file_stats).length > 0 && (
            <div>
              <h4 className="text-sm text-[#94a3b8] mb-2">Per-File Breakdown</h4>
              <div className="space-y-2">
                {Object.entries(analysisData.file_stats).map(([file, stats]) => (
                  <div
                    key={file}
                    className="flex items-center justify-between p-2 rounded-lg bg-white/5"
                  >
                    <span className="text-sm font-medium">{file}</span>
                    <div className="flex items-center gap-4 text-xs text-[#94a3b8]">
                      <span>{stats.function_count} functions</span>
                      <span>{stats.event_count} events</span>
                      <span className="text-[#6366f1]">{stats.language}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="card flex items-center gap-2 text-red-400">
          <AlertCircle size={20} />
          {error}
        </div>
      )}
    </div>
  )
}
