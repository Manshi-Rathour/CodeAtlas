
import { useState } from 'react'
import { Upload, FileArchive, X, LoaderCircle } from 'lucide-react'
import uploadService from '../../services/uploadService'

function ZipUpload({ onSuccess }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0]

    if (!selectedFile) return

    if (!selectedFile.name.toLowerCase().endsWith('.zip')) {
      setError('Please select a valid ZIP file.')
      setFile(null)
      event.target.value = ''
      return
    }

    setError('')
    setFile(selectedFile)
  }

  const handleRemoveFile = () => {
    setFile(null)
    const input = document.getElementById('project-zip-file')
    if (input) input.value = ''
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    if (!file) {
      setError('Please select a ZIP file.')
      return
    }

    setIsLoading(true)

    try {
      const project = await uploadService.uploadZip(
        { name: name.trim(), description: description.trim() },
        file
      )

      onSuccess?.(project)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Project upload failed. Please try again.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form className="import-form" onSubmit={handleSubmit}>
      <div className="import-form-heading">
        <h2>Upload your project</h2>
        <p>Import your source code directly from a ZIP archive.</p>
      </div>

      <div className="import-field">
        <label htmlFor="zip-project-name">Project name</label>
        <input
          id="zip-project-name"
          type="text"
          placeholder="e.g. My React Application"
          value={name}
          onChange={(e) => setName(e.target.value)}
          minLength={2}
          maxLength={150}
          required
        />
      </div>

      <div className="import-field">
        <label htmlFor="zip-project-description">
          Description <span>(Optional)</span>
        </label>
        <textarea
          id="zip-project-description"
          placeholder="What does your project do?"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={2000}
          rows={3}
        />
      </div>

      <div className="import-field">
        <label>Project ZIP file</label>

        {!file ? (
          <label className="zip-dropzone" htmlFor="project-zip-file">
            <div className="zip-upload-icon">
              <Upload size={25} />
            </div>
            <strong>Click to browse your files</strong>
            <span>Select a .zip archive containing your project</span>
            <input
              id="project-zip-file"
              type="file"
              accept=".zip,application/zip"
              onChange={handleFileChange}
              hidden
            />
          </label>
        ) : (
          <div className="selected-zip-file">
            <FileArchive size={25} />
            <div className="selected-zip-info">
              <strong>{file.name}</strong>
              <span>
                {(file.size / (1024 * 1024)).toFixed(2)} MB
              </span>
            </div>
            <button
              type="button"
              className="remove-zip-button"
              onClick={handleRemoveFile}
              aria-label="Remove selected ZIP file"
            >
              <X size={18} />
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="import-error" role="alert">
          {error}
        </div>
      )}

      <button
        type="submit"
        className="import-submit-button"
        disabled={isLoading || !file || name.trim().length < 2}
      >
        {isLoading ? (
          <>
            <LoaderCircle size={18} className="spin" />
            Importing project...
          </>
        ) : (
          <>
            <Upload size={18} />
            Import ZIP Project
          </>
        )}
      </button>
    </form>
  )
}

export default ZipUpload
