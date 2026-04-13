import { useState } from 'react'
import { Upload, Folder, FileCode, Zap, CheckCircle, AlertCircle } from 'lucide-react'

const LANGUAGES = [
  { id: 'python', name: 'Python', ext: '.py', color: '#3776ab' },
  { id: 'cpp', name: 'C++', ext: '.cpp', color: '#00599c' },
  { id: 'java', name: 'Java', ext: '.java', color: '#007396' },
  { id: 'go', name: 'Go', ext: '.go', color: '#00add8' },
  { id: 'rust', name: 'Rust', ext: '.rs', color: '#dea584' },
]

export default function DashboardPage({ apiUrl, sessionId, setSessionId, analysisData, setAnalysisData }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedLang, setSelectedLang] = useState('auto')
  const [uploadType, setUploadType] = useState('file') // 'file' or 'zip'

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)
    if (selectedLang !== 'auto') {
      formData.append('language', selectedLang)
    }

    try {
      const endpoint = uploadType === 'zip' ? '/batch/analyze' : '/upload'
      const response = await fetch(`${apiUrl}${endpoint}`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed')
      }

      setSessionId(data.session_id)
      setAnalysisData(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Dashboard</h2>
          <p className="text-[#94a3b8]">Upload and analyze your code projects</p>
        </div>
        {sessionId && (
          <div className="badge badge-success">
            <CheckCircle size={14} />
            Session: {sessionId.slice(0, 16)}...
          </div>
        )}
      </div>

      {/* Upload Type Selector */}
      <div className="card">
        <div className="flex gap-4 mb-4">
          <button
            onClick={() => setUploadType('file')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              uploadType === 'file' 
                ? 'bg-[#6366f1] text-white' 
                : 'bg-white/5 hover:bg-white/10'
            }`}
          >
            <FileCode size={18} />
            Single File
          </button>
          <button
            onClick={() => setUploadType('zip')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              uploadType === 'zip' 
                ? 'bg-[#6366f1] text-white' 
                : 'bg-white/5 hover:bg-white/10'
            }`}
          >
            <Folder size={18} />
            Project (ZIP)
          </button>
        </div>

        {/* Language Selector */}
        <div className="mb-4">
          <label className="text-sm text-[#94a3b8] mb-2 block">Language Detection</label>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedLang('auto')}
              className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                selectedLang === 'auto'
                  ? 'bg-[#6366f1] text-white'
                  : 'bg-white/5 hover:bg-white/10'
              }`}
            >
              <Zap size={14} className="inline mr-1" />
              Auto-detect
            </button>
            {LANGUAGES.map((lang) => (
              <button
                key={lang.id}
                onClick={() => setSelectedLang(lang.id)}
                className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                  selectedLang === lang.id
                    ? 'text-white'
                    : 'bg-white/5 hover:bg-white/10'
                }`}
                style={{
                  backgroundColor: selectedLang === lang.id ? lang.color : undefined,
                }}
              >
                {lang.name}
              </button>
            ))}
          </div>
        </div>

        {/* Upload Area */}
        <div className="border-2 border-dashed border-[rgba(255,255,255,0.2)] rounded-xl p-8 text-center hover:border-[#6366f1] transition-colors">
          <input
            type="file"
            onChange={handleFileUpload}
            accept={uploadType === 'zip' ? '.zip' : '.py,.cpp,.java,.go,.rs'}
            className="hidden"
            id="file-upload"
            disabled={loading}
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer flex flex-col items-center gap-3"
          >
            <div className="p-4 rounded-xl bg-[#6366f1]/10 text-[#6366f1]">
              <Upload size={32} />
            </div>
            <div>
              <p className="font-medium">
                {uploadType === 'zip' ? 'Upload project ZIP' : 'Upload source file'}
              </p>
              <p className="text-sm text-[#64748b] mt-1">
                {uploadType === 'zip' 
                  ? 'Drag & drop or click to select .zip file' 
                  : 'Drag & drop or click to select source file'}
              </p>
            </div>
          </label>
        </div>

        {loading && (
          <div className="flex items-center justify-center gap-2 mt-4 text-[#6366f1]">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-current"></div>
            <span>Analyzing...</span>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 mt-4 text-red-400 bg-red-500/10 p-3 rounded-lg">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Analysis Results */}
      {analysisData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card text-center">
            <div className="text-3xl font-bold text-[#6366f1]">
              {analysisData.files_analyzed || 1}
            </div>
            <div className="text-sm text-[#94a3b8] mt-1">Files Analyzed</div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-[#8b5cf6]">
              {analysisData.functions?.length || analysisData.nodes || 0}
            </div>
            <div className="text-sm text-[#94a3b8] mt-1">Functions</div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-[#ec4899]">
              {analysisData.total_events || analysisData.edges || 0}
            </div>
            <div className="text-sm text-[#94a3b8] mt-1">Trace Events</div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-[#10b981]">
              {Array.isArray(analysisData.languages) 
                ? analysisData.languages.length 
                : 1}
            </div>
            <div className="text-sm text-[#94a3b8] mt-1">Languages</div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      {sessionId && (
        <div className="card">
          <h3 className="font-semibold mb-3">Quick Actions</h3>
          <div className="flex flex-wrap gap-2">
            <a href="/graph" className="btn btn-primary">
              <Zap size={16} />
              View Graph
            </a>
            <a href="/whatif" className="btn btn-secondary">
              <Play size={16} />
              Run What-If
            </a>
            <a href="/reports" className="btn btn-secondary">
              <FileCode size={16} />
              Export Report
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
