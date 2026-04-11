import { useState } from 'react'
import { 
  Upload, 
  GitGraph, 
  Play, 
  BarChart3, 
  DollarSign, 
  FileText,
  Loader2,
  CheckCircle,
  AlertCircle,
  Zap,
  Brain,
  Layers,
  Code2
} from 'lucide-react'
import UploadTab from './components/UploadTab'
import CausalTab from './components/CausalTab'
import WhatIfTab from './components/WhatIfTab'
import BatchTab from './components/BatchTab'
import ScoreTab from './components/ScoreTab'
import ApiKeyTab from './components/ApiKeyTab'

const API_URL = 'https://code-archaeologist-7qxt.onrender.com'

function App() {
  const [activeTab, setActiveTab] = useState('upload')
  const [apiStatus, setApiStatus] = useState(null)

  // Check API status on load
  useState(() => {
    fetch(`${API_URL}/health`)
      .then(r => r.json())
      .then(data => setApiStatus(data))
      .catch(() => setApiStatus({ status: 'offline' }))
  }, [])

  const tabs = [
    { id: 'upload', name: 'Upload & Analyze', icon: Upload },
    { id: 'causal', name: 'Causal Discovery', icon: GitGraph },
    { id: 'whatif', name: 'What-If Simulator', icon: Play },
    { id: 'batch', name: 'Batch Analysis', icon: Layers },
    { id: 'score', name: 'Code Score', icon: BarChart3 },
    { id: 'apikey', name: 'API Keys', icon: DollarSign },
  ]

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-[rgba(255,255,255,0.1)] backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] text-white shadow-lg shadow-indigo-500/30">
                <Code2 size={24} />
              </div>
              <div>
                <h1 className="text-xl font-bold gradient-text">Code Archaeologist</h1>
                <p className="text-sm text-[#94a3b8]">AI-Powered Code Intelligence</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="badge badge-success">
                <span className={`w-2 h-2 rounded-full ${apiStatus?.status === 'healthy' ? 'bg-green-400 pulse' : 'bg-red-400'}`}></span>
                <span className="text-[#4ade80]">
                  API: {apiStatus?.status === 'healthy' ? 'Online' : 'Offline'}
                </span>
              </div>
              <a 
                href={`${API_URL}/docs`} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-sm text-[#6366f1] hover:text-[#8b5cf6] transition-colors"
              >
                API Docs →
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="border-b border-[rgba(255,255,255,0.1)]">
        <div className="max-w-7xl mx-auto px-4">
          <div className="tab-nav my-2">
            {tabs.map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                >
                  <Icon size={18} />
                  {tab.name}
                </button>
              )
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'upload' && <UploadTab apiUrl={API_URL} />}
        {activeTab === 'causal' && <CausalTab apiUrl={API_URL} />}
        {activeTab === 'whatif' && <WhatIfTab apiUrl={API_URL} />}
        {activeTab === 'batch' && <BatchTab apiUrl={API_URL} />}
        {activeTab === 'score' && <ScoreTab apiUrl={API_URL} />}
        {activeTab === 'apikey' && <ApiKeyTab apiUrl={API_URL} />}
      </main>

      {/* Footer */}
      <footer className="border-t border-[rgba(255,255,255,0.1)] mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between text-sm text-[#64748b]">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <Brain size={16} className="text-[#ec4899]" />
                AI-Powered Explanations
              </span>
              <span className="flex items-center gap-1">
                <Zap size={16} className="text-[#6366f1]" />
                Fast Graph Analysis
              </span>
            </div>
            <p className="text-[#64748b]">Week 4 Complete • FastAPI + React</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
