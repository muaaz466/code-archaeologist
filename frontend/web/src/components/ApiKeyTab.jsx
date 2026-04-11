import { useState } from 'react'
import { Key, DollarSign, Loader2, Copy, CheckCircle, RefreshCw, AlertTriangle, TrendingUp } from 'lucide-react'
import axios from 'axios'

export default function ApiKeyTab({ apiUrl }) {
  const [tier, setTier] = useState('free')
  const [loading, setLoading] = useState(false)
  const [apiKey, setApiKey] = useState(null)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)
  
  const [checkKey, setCheckKey] = useState('')
  const [usageData, setUsageData] = useState(null)
  const [usageLoading, setUsageLoading] = useState(false)

  const tiers = {
    free: {
      name: 'Free',
      price: '$0',
      calls: '1,000',
      features: ['Basic analysis', 'AI explanations', 'Graph queries']
    },
    standard: {
      name: 'Standard',
      price: '$19/month',
      calls: '10,000',
      features: ['Everything in Free', 'Batch analysis', 'Priority support']
    },
    enterprise: {
      name: 'Enterprise',
      price: '$99/month',
      calls: '100,000',
      features: ['Everything in Standard', 'Custom integrations', 'Dedicated support']
    }
  }

  const generateKey = async () => {
    setLoading(true)
    setError(null)
    setApiKey(null)

    try {
      const response = await axios.post(`${apiUrl}/apikey/generate?tier=${tier}`)
      setApiKey(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const checkUsage = async () => {
    if (!checkKey) return
    
    setUsageLoading(true)
    setUsageData(null)

    try {
      const response = await axios.get(`${apiUrl}/apikey/usage/${checkKey}`)
      setUsageData(response.data)
    } catch (err) {
      setUsageData({ error: err.response?.data?.detail || err.message })
    } finally {
      setUsageLoading(false)
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6">
      {/* Generate API Key */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Key size={20} className="text-primary-600" />
          Generate API Key
        </h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Plan
            </label>
            <div className="grid md:grid-cols-3 gap-4">
              {Object.entries(tiers).map(([key, t]) => (
                <div
                  key={key}
                  onClick={() => setTier(key)}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                    tier === key 
                      ? 'border-primary-600 bg-primary-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">{t.name}</span>
                    <span className="text-lg font-bold text-primary-600">{t.price}</span>
                  </div>
                  <p className="text-sm text-gray-600">{t.calls} calls/month</p>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={generateKey}
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? <Loader2 size={20} className="animate-spin" /> : <Key size={20} />}
            {loading ? 'Generating...' : `Generate ${tiers[tier].name} API Key`}
          </button>

          {error && (
            <div className="p-4 bg-red-50 text-red-700 rounded-md flex items-center gap-2">
              <AlertTriangle size={20} />
              {error}
            </div>
          )}

          {apiKey && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-md">
              <p className="font-medium text-green-900 mb-2">✅ API Key Generated!</p>
              
              <div className="flex items-center gap-2 mb-4">
                <code className="flex-1 bg-white px-3 py-2 rounded font-mono text-sm break-all">
                  {apiKey.api_key}
                </code>
                <button
                  onClick={() => copyToClipboard(apiKey.api_key)}
                  className="btn-secondary flex items-center gap-1"
                >
                  {copied ? <CheckCircle size={16} /> : <Copy size={16} />}
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Tier:</span>
                  <span className="ml-2 font-medium capitalize">{apiKey.tier}</span>
                </div>
                <div>
                  <span className="text-gray-600">Free Calls:</span>
                  <span className="ml-2 font-medium">{apiKey.free_calls_remaining}</span>
                </div>
                <div>
                  <span className="text-gray-600">Rate Limit:</span>
                  <span className="ml-2 font-medium">{apiKey.rate_limit} calls/min</span>
                </div>
                <div>
                  <span className="text-gray-600">Expires:</span>
                  <span className="ml-2 font-medium">
                    {new Date(apiKey.expires_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              <p className="text-xs text-green-700 mt-3">
                ⚠️ Copy this key now! It won't be shown again.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Check Usage */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-primary-600" />
          Check API Usage
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              API Key
            </label>
            <input
              type="text"
              value={checkKey}
              onChange={(e) => setCheckKey(e.target.value)}
              placeholder="Enter your API key..."
              className="input"
            />
          </div>

          <button
            onClick={checkUsage}
            disabled={!checkKey || usageLoading}
            className="btn-secondary w-full flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {usageLoading ? <Loader2 size={20} className="animate-spin" /> : <RefreshCw size={20} />}
            {usageLoading ? 'Checking...' : 'Check Usage'}
          </button>

          {usageData && !usageData.error && (
            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-3 rounded-lg text-center">
                  <p className="text-2xl font-bold text-blue-600">{usageData.total_calls}</p>
                  <p className="text-xs text-blue-800">Total Calls</p>
                </div>
                <div className="bg-green-50 p-3 rounded-lg text-center">
                  <p className="text-2xl font-bold text-green-600">${usageData.total_cost?.toFixed(2)}</p>
                  <p className="text-xs text-green-800">Total Cost</p>
                </div>
                <div className="bg-purple-50 p-3 rounded-lg text-center">
                  <p className="text-2xl font-bold text-purple-600">{usageData.free_calls_remaining}</p>
                  <p className="text-xs text-purple-800">Free Left</p>
                </div>
                <div className="bg-orange-50 p-3 rounded-lg text-center">
                  <p className="text-2xl font-bold text-orange-600">{usageData.rate_limit}</p>
                  <p className="text-xs text-orange-800">Rate Limit</p>
                </div>
              </div>

              {usageData.endpoint_usage && Object.keys(usageData.endpoint_usage).length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Usage by Endpoint</h4>
                  <div className="space-y-2">
                    {Object.entries(usageData.endpoint_usage).map(([endpoint, count]) => (
                      <div key={endpoint} className="flex items-center justify-between py-2 border-b">
                        <code className="text-sm bg-gray-100 px-2 py-1 rounded">{endpoint}</code>
                        <span className="font-medium">{count} calls</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {usageData?.error && (
            <div className="p-4 bg-red-50 text-red-700 rounded-md">
              {usageData.error}
            </div>
          )}
        </div>
      </div>

      {/* Pricing Info */}
      <div className="card bg-gray-50">
        <h3 className="font-semibold mb-3 flex items-center gap-2">
          <DollarSign size={18} />
          Endpoint Pricing
        </h3>
        <div className="grid md:grid-cols-2 gap-2 text-sm">
          <div className="flex justify-between py-1">
            <code className="text-gray-600">POST /upload</code>
            <span>$0.01</span>
          </div>
          <div className="flex justify-between py-1">
            <code className="text-gray-600">POST /analyze</code>
            <span>$0.01</span>
          </div>
          <div className="flex justify-between py-1">
            <code className="text-gray-600">POST /query</code>
            <span>$0.001</span>
          </div>
          <div className="flex justify-between py-1">
            <code className="text-gray-600">POST /explain</code>
            <span>$0.005</span>
          </div>
          <div className="flex justify-between py-1">
            <code className="text-gray-600">POST /causal/discover</code>
            <span>$0.01</span>
          </div>
          <div className="flex justify-between py-1">
            <code className="text-gray-600">POST /whatif/simulate</code>
            <span>$0.005</span>
          </div>
          <div className="flex justify-between py-1">
            <code className="text-gray-600">POST /batch/analyze</code>
            <span>$0.05</span>
          </div>
          <div className="flex justify-between py-1">
            <code className="text-gray-600">GET /score/*</code>
            <span>$0.001</span>
          </div>
        </div>
      </div>
    </div>
  )
}
