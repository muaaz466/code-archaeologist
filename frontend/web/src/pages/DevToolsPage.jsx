import { useState } from 'react'
import { Terminal, Webhook, Code, Book, Copy, CheckCircle } from 'lucide-react'

const API_BASE = 'https://code-archaeologist-7qxt.onrender.com'

const CLI_EXAMPLE = `pip install code-archaeologist

codearch analyze myproject.py
codearch batch myproject.zip
codearch query --session <id> --function "main"
codearch export --session <id> --pdf report.pdf`

const CURL_EXAMPLE = `# Upload single file
curl -X POST ${API_BASE}/upload \\
  -F "file=@myproject.py"

# Batch upload
curl -X POST ${API_BASE}/batch/analyze \\
  -F "file=@project.zip"

# Query graph
curl "${API_BASE}/query/{session_id}?query_type=callers&function=main"

# Export PDF
curl "${API_BASE}/export/pdf?session_id={session_id}" \\
  -o report.pdf`

const WEBHOOK_EXAMPLE = `# GitHub Actions Example
name: Code Analysis
on: [push]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Analyze Code
        run: |
          curl -X POST ${API_BASE}/batch/analyze \\
            -F "file=@project.zip" \\
            -H "X-API-Key: \${{ secrets.CODEARCH_API_KEY }}"
      
      - name: Check What-If Impact
        run: |
          curl -X POST "${API_BASE}/whatif/{session_id}?function=critical_func"`

export default function DevToolsPage({ apiUrl }) {
  const [copied, setCopied] = useState(false)
  const [activeTab, setActiveTab] = useState('cli')

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const tabs = [
    { id: 'cli', name: 'CLI Tool', icon: Terminal },
    { id: 'api', name: 'API / cURL', icon: Code },
    { id: 'webhook', name: 'CI/CD', icon: Webhook },
    { id: 'docs', name: 'Documentation', icon: Book },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold">Developer Tools</h2>
        <p className="text-[#94a3b8]">CLI, API integration, and CI/CD configuration</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-white/10 pb-2">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-[#6366f1] text-white'
                  : 'hover:bg-white/5 text-[#94a3b8]'
              }`}
            >
              <Icon size={16} />
              {tab.name}
            </button>
          )
        })}
      </div>

      {/* CLI Tab */}
      {activeTab === 'cli' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Command Line Interface</h3>
            <button
              onClick={() => copyToClipboard(CLI_EXAMPLE)}
              className="flex items-center gap-1 text-sm text-[#6366f1] hover:text-[#8b5cf6]"
            >
              {copied ? <CheckCircle size={16} /> : <Copy size={16} />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <pre className="bg-[#0f172a] p-4 rounded-lg overflow-x-auto text-sm font-mono">
            <code>{CLI_EXAMPLE}</code>
          </pre>
          <div className="mt-4 space-y-2 text-sm text-[#94a3b8]">
            <p>
              <strong className="text-white">Install:</strong> pip install code-archaeologist
            </p>
            <p>
              <strong className="text-white">Analyze:</strong> Single file or batch ZIP
            </p>
            <p>
              <strong className="text-white">Query:</strong> Find callers, callees, paths
            </p>
            <p>
              <strong className="text-white">Export:</strong> PDF or JSON reports
            </p>
          </div>
        </div>
      )}

      {/* API Tab */}
      {activeTab === 'api' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">REST API (cURL)</h3>
            <button
              onClick={() => copyToClipboard(CURL_EXAMPLE)}
              className="flex items-center gap-1 text-sm text-[#6366f1] hover:text-[#8b5cf6]"
            >
              {copied ? <CheckCircle size={16} /> : <Copy size={16} />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <pre className="bg-[#0f172a] p-4 rounded-lg overflow-x-auto text-sm font-mono">
            <code>{CURL_EXAMPLE}</code>
          </pre>
          <div className="mt-4">
            <h4 className="font-medium mb-2">Available Endpoints:</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
              <div className="p-2 rounded bg-white/5">
                <code className="text-[#10b981]">POST /upload</code>
                <p className="text-[#94a3b8] text-xs mt-1">Upload single file</p>
              </div>
              <div className="p-2 rounded bg-white/5">
                <code className="text-[#10b981]">POST /batch/analyze</code>
                <p className="text-[#94a3b8] text-xs mt-1">Upload ZIP batch</p>
              </div>
              <div className="p-2 rounded bg-white/5">
                <code className="text-[#8b5cf6]">GET /query/&#123;id&#125;</code>
                <p className="text-[#94a3b8] text-xs mt-1">Query call graph</p>
              </div>
              <div className="p-2 rounded bg-white/5">
                <code className="text-[#8b5cf6]">GET /explain/&#123;id&#125;</code>
                <p className="text-[#94a3b8] text-xs mt-1">AI function explanation</p>
              </div>
              <div className="p-2 rounded bg-white/5">
                <code className="text-[#ec4899]">POST /whatif/&#123;id&#125;</code>
                <p className="text-[#94a3b8] text-xs mt-1">Simulate function removal</p>
              </div>
              <div className="p-2 rounded bg-white/5">
                <code className="text-[#f59e0b]">GET /export/pdf</code>
                <p className="text-[#94a3b8] text-xs mt-1">Export PDF report</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CI/CD Tab */}
      {activeTab === 'webhook' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">CI/CD Integration</h3>
            <button
              onClick={() => copyToClipboard(WEBHOOK_EXAMPLE)}
              className="flex items-center gap-1 text-sm text-[#6366f1] hover:text-[#8b5cf6]"
            >
              {copied ? <CheckCircle size={16} /> : <Copy size={16} />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <pre className="bg-[#0f172a] p-4 rounded-lg overflow-x-auto text-sm font-mono">
            <code>{WEBHOOK_EXAMPLE}</code>
          </pre>
          <div className="mt-4 space-y-2 text-sm text-[#94a3b8]">
            <p>
              <strong className="text-white">GitHub Actions:</strong> Run analysis on every push
            </p>
            <p>
              <strong className="text-white">GitLab CI:</strong> Similar pipeline configuration
            </p>
            <p>
              <strong className="text-white">Jenkins:</strong> Use curl in pipeline steps
            </p>
            <p>
              <strong className="text-white">What-If:</strong> Check impact of changes before merging
            </p>
          </div>
        </div>
      )}

      {/* Docs Tab */}
      {activeTab === 'docs' && (
        <div className="card">
          <h3 className="font-semibold mb-4">Documentation</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a
              href={`${apiUrl}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 rounded-xl bg-[#6366f1]/10 hover:bg-[#6366f1]/20 transition-colors"
            >
              <Book size={24} className="text-[#6366f1] mb-2" />
              <h4 className="font-medium">API Reference</h4>
              <p className="text-sm text-[#94a3b8]">Interactive Swagger docs</p>
            </a>
            <a
              href="https://github.com/muaaz466/code-archaeologist"
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
            >
              <Code size={24} className="text-[#8b5cf6] mb-2" />
              <h4 className="font-medium">GitHub Repository</h4>
              <p className="text-sm text-[#94a3b8]">Source code & examples</p>
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
