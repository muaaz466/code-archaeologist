import { useState } from 'react'
import { Upload, FileCode, Loader2, Search, Brain, FileText } from 'lucide-react'
import axios from 'axios'

export default function UploadTab({ apiUrl }) {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [queryFunction, setQueryFunction] = useState('')
  const [queryResult, setQueryResult] = useState(null)
  const [explainFunction, setExplainFunction] = useState('')
  const [explanation, setExplanation] = useState(null)

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file) return

    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${apiUrl}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleQuery = async () => {
    if (!queryFunction || !result?.session_id) return
    
    try {
      // Query both callers and callees
      const [callersRes, calleesRes] = await Promise.all([
        axios.post(`${apiUrl}/query/${result.session_id}`, {
          query_type: "callers",
          target: queryFunction
        }),
        axios.post(`${apiUrl}/query/${result.session_id}`, {
          query_type: "callees",
          target: queryFunction
        })
      ])
      
      setQueryResult({
        callers: callersRes.data,
        callees: calleesRes.data
      })
    } catch (err) {
      setQueryResult({ error: err.response?.data?.detail || err.message })
    }
  }

  const handleExplain = async () => {
    if (!explainFunction || !result?.session_id) return
    
    try {
      const response = await axios.post(`${apiUrl}/explain`, {
        session_id: result.session_id,
        function_name: explainFunction
      })
      setExplanation(response.data)
    } catch (err) {
      setExplanation({ error: err.response?.data?.detail || err.message })
    }
  }

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="card">
        <div className="section-header">
          <Upload size={24} className="text-[#6366f1]" />
          <h2 className="section-title">Upload Python File</h2>
        </div>
        
        <form onSubmit={handleUpload} className="space-y-4">
          <div className="drop-zone">
            <input
              type="file"
              accept=".py"
              onChange={(e) => setFile(e.target.files[0])}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <FileCode size={64} className="mx-auto text-[#6366f1] mb-4" />
              <p className="text-[#94a3b8] text-lg">
                {file ? file.name : 'Click to upload or drag and drop'}
              </p>
              <p className="text-sm text-[#64748b] mt-2">Python files only (.py)</p>
            </label>
          </div>
          
          <button
            type="submit"
            disabled={!file || loading}
            className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? <Loader2 size={20} className="animate-spin" /> : <Upload size={20} />}
            {loading ? 'Analyzing...' : 'Upload & Analyze'}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-500/20 border border-red-500/30 rounded-xl flex items-center gap-2 text-red-300">
            <span className="text-xl">⚠️</span> {error}
          </div>
        )}

        {result && (
          <div className="mt-4 p-4 bg-green-500/20 border border-green-500/30 rounded-xl">
            <p className="font-semibold text-green-400">✅ Analysis Complete!</p>
            <p className="text-sm text-[#94a3b8] mt-1">Session ID: {result.session_id}</p>
            <p className="text-sm text-[#94a3b8]">Functions found: {result.functions?.length || 0}</p>
          </div>
        )}
      </div>

      {/* Query Section */}
      {result && (
        <div className="card">
          <div className="section-header">
            <Search size={24} className="text-[#6366f1]" />
            <h2 className="section-title">Query Graph</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#94a3b8] mb-2">
                Available Functions
              </label>
              <select
                value={queryFunction}
                onChange={(e) => setQueryFunction(e.target.value)}
                className="input"
              >
                <option value="">Select a function...</option>
                {result.functions?.map(fn => (
                  <option key={fn} value={fn}>{fn}</option>
                ))}
              </select>
            </div>
            
            <button
              onClick={handleQuery}
              disabled={!queryFunction}
              className="btn-primary flex items-center gap-2 disabled:opacity-50"
            >
              <Search size={18} />
              Get Callers & Callees
            </button>

            {queryResult && !queryResult.error && (
              <div className="mt-4 space-y-3">
                <div className="p-4 bg-blue-500/20 border border-blue-500/30 rounded-xl">
                  <p className="font-semibold text-blue-400">Callers (incoming):</p>
                  <p className="text-[#94a3b8]">{queryResult.callers?.results?.join(', ') || 'None'}</p>
                </div>
                <div className="p-4 bg-green-500/20 border border-green-500/30 rounded-xl">
                  <p className="font-semibold text-green-400">Callees (outgoing):</p>
                  <p className="text-[#94a3b8]">{queryResult.callees?.results?.join(', ') || 'None'}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* AI Explain Section */}
      {result && (
        <div className="card">
          <div className="section-header">
            <Brain size={24} className="text-[#ec4899]" />
            <h2 className="section-title">AI Explanation</h2>
          </div>
          
          <div className="space-y-4">
            <select
              value={explainFunction}
              onChange={(e) => setExplainFunction(e.target.value)}
              className="input"
            >
              <option value="">Select a function to explain...</option>
              {result.functions?.map(fn => (
                <option key={fn} value={fn}>{fn}</option>
              ))}
            </select>
            
            <button
              onClick={handleExplain}
              disabled={!explainFunction}
              className="btn-primary flex items-center gap-2 disabled:opacity-50"
            >
              <Brain size={18} />
              Get AI Explanation
            </button>

            {explanation && !explanation.error && (
              <div className="mt-4 p-4 bg-[#ec4899]/20 border border-[#ec4899]/30 rounded-xl">
                <h3 className="font-semibold text-[#ec4899] mb-2">
                  {explanation.function}
                </h3>
                <p className="text-[#94a3b8]">{explanation.explanation}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {explanation.tags?.map(tag => (
                    <span key={tag} className="px-3 py-1 bg-[#ec4899]/30 text-[#ec4899] text-xs rounded-full">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
