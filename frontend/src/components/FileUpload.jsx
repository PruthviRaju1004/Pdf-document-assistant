import { useState } from 'react'

export default function FileUpload({ apiKey, onUploadSuccess }) {
  const [file, setFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState('')

  const handleUpload = async () => {
    if (!file || !apiKey) return

    setIsUploading(true)
    setError('')

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://127.0.0.1:8000/upload', {
        method: 'POST',
        headers: { 'X-API-Key': apiKey },
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const data = await response.json()
      onUploadSuccess(data)
      setFile(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="flex flex-col gap-2 w-full max-w-md">
      <input
        type="file"
        accept=".pdf"
        onChange={(e) => setFile(e.target.files[0])}
        className="text-sm"
      />
      <button
        onClick={handleUpload}
        disabled={!file || isUploading}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        {isUploading ? 'Uploading...' : 'Upload PDF'}
      </button>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  )
}