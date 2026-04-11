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
      const response = await axios.post(`${apiUrl}/query/${result.session_id}`, {
        function_name: queryFunction
      })
      setQueryResult(response.data)
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
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Upload size={20} className="text-primary-600" />
          Upload Python File
        </h2>
        
        <form onSubmit={handleUpload} className="space-y-4">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-primary-500 transition-colors">
            <input
              type="file"
              accept=".py"
              onChange={(e) => setFile(e.target.files[0])}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <FileCode size={48} className="mx-auto text-gray-400 mb-2" />
              <p className="text-gray-600">
                {file ? file.name : 'Click to upload or drag and drop'}
              </p>
              <p className="text-sm text-gray-400">Python files only (.py)</p>
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
          <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-md flex items-center gap-2">
            <span className="text-xl">⚠️</span> {error}
          </div>
        )}

        {result && (
          <div className="mt-4 p-4 bg-green-50 text-green-700 rounded-md">
            <p className="font-medium">✅ Analysis Complete!</p>
            <p className="text-sm mt-1">Session ID: {result.session_id}</p>
            <p className="text-sm">Functions found: {result.functions?.length || 0}</p>
          </div>
        )}
      </div>

      {/* Query Section */}
      {result && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Search size={20} className="text-primary-600" />
            Query Graph
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
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
                <div className="p-3 bg-blue-50 rounded-md">
                  <p className="font-medium text-blue-900">Callers (incoming):</p>
                  <p className="text-blue-700">{queryResult.callers?.join(', ') || 'None'}</p>
                </div>
                <div className="p-3 bg-green-50 rounded-md">
                  <p className="font-medium text-green-900">Callees (outgoing):</p>
                  <p className="text-green-700">{queryResult.callees?.join(', ') || 'None'}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* AI Explain Section */}
      {result && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Brain size={20} className="text-primary-600" />
            AI Explanation
          </h2>
          
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
              <div className="mt-4 p-4 bg-purple-50 rounded-md">
                <h3 className="font-medium text-purple-900 mb-2">
                  {explanation.function}
                </h3>
                <p className="text-purple-800">{explanation.explanation}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {explanation.tags?.map(tag => (
                    <span key={tag} className="px-2 py-1 bg-purple-200 text-purple-800 text-xs rounded">
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
