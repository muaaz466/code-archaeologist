import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom'
import { 
  LayoutDashboard,
  GitGraph, 
  Play,
  FileText,
  Terminal,
  Code2,
  Brain,
  Zap,
  Menu,
  X
} from 'lucide-react'

// Page Components
import DashboardPage from './pages/DashboardPage'
import GraphViewPage from './pages/GraphViewPage'
import WhatIfPage from './pages/WhatIfPage'
import ReportsPage from './pages/ReportsPage'
import DevToolsPage from './pages/DevToolsPage'

const API_URL = 'https://code-archaeologist-7qxt.onrender.com'

// Navigation items
const navItems = [
  { path: '/', name: 'Dashboard', icon: LayoutDashboard, description: 'Upload & Analyze Projects' },
  { path: '/graph', name: 'Graph View', icon: GitGraph, description: 'Interactive Causal Graph' },
  { path: '/whatif', name: 'What-If', icon: Play, description: 'Simulate Function Removal' },
  { path: '/reports', name: 'Reports', icon: FileText, description: 'PDF Export & Analysis' },
  { path: '/devtools', name: 'Dev Tools', icon: Terminal, description: 'API, CLI & CI/CD' },
]

// Header Component
function Header({ apiStatus }) {
  return (
    <header className="border-b border-[rgba(255,255,255,0.1)] backdrop-blur-md sticky top-0 z-50 bg-[#0f172a]/80">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <NavLink to="/" className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] text-white shadow-lg shadow-indigo-500/30">
              <Code2 size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold gradient-text">Code Archaeologist</h1>
              <p className="text-sm text-[#94a3b8]">AI-Powered Code Intelligence</p>
            </div>
          </NavLink>
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
              className="text-sm text-[#6366f1] hover:text-[#8b5cf6] transition-colors hidden sm:block"
            >
              API Docs →
            </a>
          </div>
        </div>
      </div>
    </header>
  )
}

// Sidebar Navigation
function Sidebar({ mobileOpen, setMobileOpen }) {
  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-64 bg-[#1e293b] border-r border-[rgba(255,255,255,0.1)]
        transform transition-transform duration-200 ease-in-out
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="p-4 lg:hidden">
          <button 
            onClick={() => setMobileOpen(false)}
            className="p-2 rounded-lg hover:bg-white/10"
          >
            <X size={24} />
          </button>
        </div>
        
        <nav className="p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) => `
                  flex flex-col p-3 rounded-xl transition-all duration-200
                  ${isActive 
                    ? 'bg-gradient-to-r from-[#6366f1]/20 to-[#8b5cf6]/20 border border-[#6366f1]/30' 
                    : 'hover:bg-white/5'
                  }
                `}
              >
                <div className="flex items-center gap-3">
                  <Icon size={20} className="text-[#6366f1]" />
                  <span className="font-medium">{item.name}</span>
                </div>
                <span className="text-xs text-[#94a3b8] ml-8 mt-1">
                  {item.description}
                </span>
              </NavLink>
            )
          })}
        </nav>
        
        {/* Footer in sidebar */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[rgba(255,255,255,0.1)]">
          <div className="flex items-center gap-2 text-sm text-[#64748b]">
            <Brain size={16} className="text-[#ec4899]" />
            <span>AI-Powered</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-[#64748b] mt-2">
            <Zap size={16} className="text-[#6366f1]" />
            <span>Fast Analysis</span>
          </div>
        </div>
      </aside>
    </>
  )
}

// Main Layout
function Layout({ children, apiStatus }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  
  return (
    <div className="min-h-screen bg-[#0f172a] text-white">
      <Header apiStatus={apiStatus} />
      
      {/* Mobile menu button */}
      <div className="lg:hidden px-4 py-2 border-b border-[rgba(255,255,255,0.1)]">
        <button 
          onClick={() => setMobileOpen(true)}
          className="p-2 rounded-lg hover:bg-white/10 flex items-center gap-2"
        >
          <Menu size={20} />
          <span className="text-sm">Menu</span>
        </button>
      </div>
      
      <div className="flex max-w-7xl mx-auto">
        <Sidebar mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />
        
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}

function App() {
  const [apiStatus, setApiStatus] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [analysisData, setAnalysisData] = useState(null)
  const [appError, setAppError] = useState(null)

  useEffect(() => {
    try {
      fetch(`${API_URL}/health`)
        .then(r => r.json())
        .then(data => setApiStatus(data))
        .catch(() => setApiStatus({ status: 'offline' }))
    } catch (err) {
      console.error('App init error:', err)
      setAppError(err.message)
    }
  }, [])

  if (appError) {
    return (
      <div style={{padding: '20px', color: 'white', background: '#0f172a', minHeight: '100vh'}}>
        <h1>Error Loading App</h1>
        <p style={{color: '#ef4444'}}>{appError}</p>
        <pre style={{background: '#1e293b', padding: '10px', marginTop: '20px'}}>
          Check console for details
        </pre>
      </div>
    )
  }

  return (
    <Router>
      <Layout apiStatus={apiStatus}>
        <div style={{padding: '20px'}}>
          <h1>TEST: React is rendering!</h1>
          <p>API Status: {apiStatus?.status || 'checking...'}</p>
        </div>
        <Routes>
          <Route 
            path="/" 
            element={
              <DashboardPage 
                apiUrl={API_URL} 
                sessionId={sessionId}
                setSessionId={setSessionId}
                analysisData={analysisData}
                setAnalysisData={setAnalysisData}
              />
            } 
          />
          <Route 
            path="/graph" 
            element={
              <GraphViewPage 
                apiUrl={API_URL} 
                sessionId={sessionId}
                analysisData={analysisData}
              />
            } 
          />
          <Route 
            path="/whatif" 
            element={
              <WhatIfPage 
                apiUrl={API_URL} 
                sessionId={sessionId}
                analysisData={analysisData}
              />
            } 
          />
          <Route 
            path="/reports" 
            element={
              <ReportsPage 
                apiUrl={API_URL} 
                sessionId={sessionId}
                analysisData={analysisData}
              />
            } 
          />
          <Route 
            path="/devtools" 
            element={<DevToolsPage apiUrl={API_URL} />} 
          />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
