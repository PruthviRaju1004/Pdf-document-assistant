import { useState, useEffect } from 'react'

export default function ApiKeyInput({ onKeyChange }) {
  const [apiKey, setApiKey] = useState('')

  useEffect(() => {
    const saved = localStorage.getItem('doc-assistant-api-key')
    if (saved) {
      setApiKey(saved)
      onKeyChange(saved)
    }
  }, [])

  const handleChange = (e) => {
    const value = e.target.value
    setApiKey(value)
    localStorage.setItem('doc-assistant-api-key', value)
    onKeyChange(value)
  }

  return (
    <div className="flex flex-col gap-1 w-full max-w-md">
      <label className="text-sm font-medium text-zinc-600">API Key</label>
      <input
        type="password"
        value={apiKey}
        onChange={handleChange}
        placeholder="test-key-456"
        className="border border-zinc-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
      />
    </div>
  )
}   