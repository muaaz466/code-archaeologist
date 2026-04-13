import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// Global error handler
window.onerror = function(msg, url, line, col, error) {
  const root = document.getElementById('root')
  if (root) {
    root.innerHTML = `
      <div style="padding: 20px; color: white; background: #0f172a; font-family: sans-serif;">
        <h2 style="color: #ef4444;">Runtime Error</h2>
        <p>${msg}</p>
        <p>Line: ${line}</p>
        <pre style="background: #1e293b; padding: 10px; overflow: auto;">${error?.stack || ''}</pre>
      </div>
    `
  }
  return false
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
