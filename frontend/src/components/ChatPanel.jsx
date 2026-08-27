import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

export default function ChatPanel({ apiKey }) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!question.trim() || !apiKey || isLoading) return

    setIsLoading(true)
    setError('')

    try {
      const response = await fetch('http://127.0.0.1:8000/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify({
          question: question,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Request failed')
      }

      const data = await response.json()
      setAnswer(data.answer)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-xl shadow-md border border-zinc-200">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your documents..."
          className="flex-1 px-4 py-2 bg-zinc-50 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={!question.trim() || isLoading}
          className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-300 disabled:cursor-not-allowed text-white font-medium rounded-lg"
        >
          {isLoading ? 'Thinking…' : 'Ask'}
        </button>
      </form>

      {isLoading && (
        <div className="mt-6 flex items-center gap-2 text-zinc-500 text-sm">
          <span className="h-2 w-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
          <span className="h-2 w-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
          <span className="h-2 w-2 bg-blue-500 rounded-full animate-bounce" />
        </div>
      )}

      {error && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {answer && !isLoading && (
        <div className="mt-6 p-4 bg-zinc-50 border border-zinc-200 rounded-lg">
          <h4 className="text-sm font-semibold text-zinc-500 uppercase tracking-wider mb-2">Answer</h4>
          <div className="prose prose-sm max-w-none prose-zinc">
            <ReactMarkdown>{answer}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  )
}