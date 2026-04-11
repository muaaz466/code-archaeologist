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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-primary-600 text-white p-2 rounded-lg">
                <Code2 size={24} />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Code Archaeologist</h1>
                <p className="text-sm text-gray-500">Week 4 - AI-Powered Code Intelligence</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm">
                <span className={`w-2 h-2 rounded-full ${apiStatus?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`}></span>
                <span className="text-gray-600">
                  API: {apiStatus?.status === 'healthy' ? 'Online' : 'Offline'}
                </span>
              </div>
              <a 
                href={`${API_URL}/docs`} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                API Docs →
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1 overflow-x-auto">
            {tabs.map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
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
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <Brain size={16} />
                AI-Powered Explanations
              </span>
              <span className="flex items-center gap-1">
                <Zap size={16} />
                Fast Graph Analysis
              </span>
            </div>
            <p>Week 4 Complete • FastAPI + React</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
