import { useState } from 'react'
import ApiKeyInput from './components/ApiKeyInput'
import FileUpload from './components/FileUpload'
import ChatPanel from './components/ChatPanel'

function App() {
  const [apiKey, setApiKey] = useState('')
  const [documents, setDocuments] = useState([])

  const handleUploadSuccess = (data) => {
    setDocuments((prev) => [...prev, data])
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center p-8 gap-4">
      <h1 className="text-2xl font-bold text-gray-800">Document Assistant</h1>
      <ApiKeyInput onKeyChange={setApiKey} />
      <FileUpload apiKey={apiKey} onUploadSuccess={handleUploadSuccess} />
      {documents.length > 0 && (
        <div className="text-sm text-gray-600">
          Active documents: {documents.map((d) => d.filename).join(', ')}
        </div>
      )}
      <ChatPanel apiKey={apiKey} documentPaths={documents.map((d) => d.path)} />
    </div>
  )
}

export default App