
import { useState } from 'react'
import {
  GitBranch,
  Code2,
  Link,
  LoaderCircle,
  Download,
} from 'lucide-react'
import uploadService from '../../services/uploadService'

function GitHubImport({ onSuccess }) {
  const [repositoryUrl, setRepositoryUrl] = useState('')
  const [branch, setBranch] = useState('main')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    const trimmedUrl = repositoryUrl.trim()

    if (
      !/^https:\/\/github\.com\/[^/]+\/[^/]+\/?$/.test(trimmedUrl)
    ) {
      setError(
        'Enter a valid public GitHub repository URL.'
      )
      return
    }

    if (!branch.trim()) {
      setError('Please enter a branch name.')
      return
    }

    setIsLoading(true)

    try {
      const project = await uploadService.importGitHub({
        repository_url: trimmedUrl,
        branch: branch.trim(),
        name: name.trim() || null,
        description: description.trim() || null,
      })

      onSuccess?.(project)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'GitHub import failed. Please check the repository URL and branch.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form className="import-form" onSubmit={handleSubmit}>
      <div className="import-form-heading">
        <h2>Import from GitHub</h2>
        <p>
          Connect a public repository and let CodeAtlas
          analyze its source files.
        </p>
      </div>

      <div className="import-field">
        <label htmlFor="github-repository-url">
          Repository URL
        </label>

        <div className="import-input-with-icon">
          <Link size={18} />
          <input
            id="github-repository-url"
            type="url"
            placeholder="https://github.com/username/repository"
            value={repositoryUrl}
            onChange={(e) => setRepositoryUrl(e.target.value)}
            required
          />
        </div>
      </div>

      <div className="import-field">
        <label htmlFor="github-branch">Branch</label>

        <div className="import-input-with-icon">
          <GitBranch size={18} />
          <input
            id="github-branch"
            type="text"
            placeholder="main"
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            maxLength={255}
            required
          />
        </div>
        <span className="import-field-hint">
          Enter the branch you want to import, such as main or develop.
        </span>
      </div>

      <div className="import-field">
        <label htmlFor="github-project-name">
          Project name <span>(Optional)</span>
        </label>
        <input
          id="github-project-name"
          type="text"
          placeholder="Automatically detected from repository"
          value={name}
          onChange={(e) => setName(e.target.value)}
          minLength={2}
          maxLength={150}
        />
      </div>

      <div className="import-field">
        <label htmlFor="github-project-description">
          Description <span>(Optional)</span>
        </label>
        <textarea
          id="github-project-description"
          placeholder="Describe your project..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={2000}
          rows={3}
        />
      </div>

      {error && (
        <div className="import-error" role="alert">
          {error}
        </div>
      )}

      <button
        type="submit"
        className="import-submit-button"
        disabled={isLoading || !repositoryUrl.trim()}
      >
        {isLoading ? (
          <>
            <LoaderCircle size={18} className="spin" />
            Importing repository...
          </>
        ) : (
          <>
            <Download size={18} />
            Import GitHub Repository
          </>
        )}
      </button>

      <div className="github-import-note">
        <Code2 size={16} />
        Only public GitHub repositories are supported currently.
      </div>
    </form>
  )
}

export default GitHubImport
