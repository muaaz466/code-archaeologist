import { useState } from 'react'
import { Layers, Upload, Loader2, FileArchive, GitCompare, AlertCircle } from 'lucide-react'
import axios from 'axios'

export default function BatchTab({ apiUrl }) {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [compareMode, setCompareMode] = useState(false)
  const [baselineId, setBaselineId] = useState('')
  const [currentId, setCurrentId] = useState('')
  const [compareResult, setCompareResult] = useState(null)

  const handleBatchUpload = async (e) => {
    e.preventDefault()
    if (!file) return

    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${apiUrl}/batch/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCompare = async () => {
    if (!baselineId || !currentId) return

    setLoading(true)
    setError(null)
    setCompareResult(null)

    try {
      const response = await axios.post(
        `${apiUrl}/batch/compare?baseline_id=${baselineId}&current_id=${currentId}`
      )
      setCompareResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setCompareMode(false)}
          className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
            !compareMode ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-700'
          }`}
        >
          <Upload size={18} />
          Batch Upload
        </button>
        <button
          onClick={() => setCompareMode(true)}
          className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
            compareMode ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-700'
          }`}
        >
          <GitCompare size={18} />
          Compare Runs
        </button>
      </div>

      {!compareMode ? (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Layers size={20} className="text-primary-600" />
            Batch Analysis
          </h2>
          <p className="text-gray-600 mb-4">
            Upload a ZIP file containing multiple source files. We'll analyze all files 
            and build a combined causal graph across your entire codebase.
          </p>
          <p className="text-sm text-gray-500 mb-4">
            Supports: Python (.py), Java (.java), Go (.go), Rust (.rs), C/C++ (.c, .cpp, .h)
          </p>

          <form onSubmit={handleBatchUpload} className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-500 transition-colors">
              <input
                type="file"
                accept=".zip"
                onChange={(e) => setFile(e.target.files[0])}
                className="hidden"
                id="zip-upload"
              />
              <label htmlFor="zip-upload" className="cursor-pointer">
                <FileArchive size={64} className="mx-auto text-gray-400 mb-3" />
                <p className="text-gray-600 font-medium">
                  {file ? file.name : 'Drop ZIP file here or click to upload'}
                </p>
                <p className="text-sm text-gray-400 mt-1">Maximum file size: 50MB</p>
              </label>
            </div>

            <button
              type="submit"
              disabled={!file || loading}
              className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? <Loader2 size={20} className="animate-spin" /> : <Upload size={20} />}
              {loading ? 'Analyzing...' : 'Analyze Batch'}
            </button>
          </form>

          {error && (
            <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-md flex items-center gap-2">
              <AlertCircle size={20} />
              {error}
            </div>
          )}

          {result && (
            <div className="mt-6 space-y-4">
              <div className="p-4 bg-green-500/20 border border-green-500/30 rounded-xl">
                <p className="font-semibold text-green-400">✅ Batch Analysis Complete!</p>
                <p className="text-sm mt-1 text-[#94a3b8]">Session ID: {result.session_id}</p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="stat-card card">
                  <p className="stat-value">{result.files_analyzed || 0}</p>
                  <p className="stat-label">Files Analyzed</p>
                </div>
                <div className="stat-card card">
                  <p className="stat-value">{(result.functions_found?.length || result.total_functions) || 0}</p>
                  <p className="stat-label">Functions</p>
                </div>
                <div className="stat-card card">
                  <p className="stat-value">{result.total_events || 0}</p>
                  <p className="stat-label">Trace Events</p>
                </div>
                <div className="stat-card card">
                  <p className="stat-value">{(result.languages?.length || 0)}</p>
                  <p className="stat-label">Languages</p>
                </div>
              </div>

              {result.languages && result.languages.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2 text-[#94a3b8]">Languages Detected</h4>
                  <div className="flex flex-wrap gap-2">
                    {result.languages.map((lang) => (
                      <span
                        key={lang}
                        className="px-3 py-1 bg-[#6366f1]/20 text-[#6366f1] rounded-full text-sm"
                      >
                        {lang}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <GitCompare size={20} className="text-primary-600" />
            Compare Runs
          </h2>
          <p className="text-gray-600 mb-4">
            Compare two analysis sessions to see what changed between versions.
            Useful for before/after refactor comparisons.
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Baseline Session ID (Before)
              </label>
              <input
                type="text"
                value={baselineId}
                onChange={(e) => setBaselineId(e.target.value)}
                placeholder="e.g., sess_abc123"
                className="input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Current Session ID (After)
              </label>
              <input
                type="text"
                value={currentId}
                onChange={(e) => setCurrentId(e.target.value)}
                placeholder="e.g., sess_xyz789"
                className="input"
              />
            </div>

            <button
              onClick={handleCompare}
              disabled={!baselineId || !currentId || loading}
              className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? <Loader2 size={20} className="animate-spin" /> : <GitCompare size={20} />}
              {loading ? 'Comparing...' : 'Compare Sessions'}
            </button>
          </div>

          {compareResult && (
            <div className="mt-6 space-y-4">
              <h3 className="font-semibold">Comparison Results</h3>
              
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-green-50 p-3 rounded-lg text-center">
                  <p className="text-xl font-bold text-green-600">
                    {compareResult.changes?.functions_added?.length || 0}
                  </p>
                  <p className="text-xs text-green-800">Functions Added</p>
                </div>
                <div className="bg-red-50 p-3 rounded-lg text-center">
                  <p className="text-xl font-bold text-red-600">
                    {compareResult.changes?.functions_removed?.length || 0}
                  </p>
                  <p className="text-xs text-red-800">Functions Removed</p>
                </div>
                <div className="bg-blue-50 p-3 rounded-lg text-center">
                  <p className="text-xl font-bold text-blue-600">
                    {compareResult.changes?.call_graph_changes || 0}
                  </p>
                  <p className="text-xs text-blue-800">Call Graph Changes</p>
                </div>
              </div>

              {compareResult.impact?.breaking_changes?.length > 0 && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                  <h4 className="font-medium text-red-900 mb-2">⚠️ Potential Breaking Changes</h4>
                  <ul className="space-y-1 text-red-800 text-sm">
                    {compareResult.impact.breaking_changes.map((change, idx) => (
                      <li key={idx}>• {change}</li>
                    ))}
                  </ul>
                </div>
              )}

              {compareResult.impact?.risk_level && (
                <div className={`p-4 rounded-md ${
                  compareResult.impact.risk_level === 'high' ? 'bg-red-50 text-red-700' :
                  compareResult.impact.risk_level === 'medium' ? 'bg-yellow-50 text-yellow-700' :
                  'bg-green-50 text-green-700'
                }`}>
                  <p className="font-medium">
                    Risk Level: {compareResult.impact.risk_level.toUpperCase()}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
