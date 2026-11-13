import Editor from '@monaco-editor/react'
import {
  FileCode2,
  Copy,
  Check,
  Maximize2,
  Minimize2,
} from 'lucide-react'
import { useState } from 'react'

function CodeViewer({ file, content, isLoading, error }) {
  const [copied, setCopied] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const getEditorLanguage = (language) => {
    const languageMap = {
      Python: 'python',
      JavaScript: 'javascript',
      TypeScript: 'typescript',
      Java: 'java',
      'C++': 'cpp',
      C: 'c',
      'C#': 'csharp',
      Go: 'go',
      Rust: 'rust',
      PHP: 'php',
      Ruby: 'ruby',
      Swift: 'swift',
      HTML: 'html',
      CSS: 'css',
      SCSS: 'scss',
      JSON: 'json',
      YAML: 'yaml',
      Markdown: 'markdown',
      SQL: 'sql',
      Shell: 'shell',
      Dockerfile: 'dockerfile',
      XML: 'xml',
      GraphQL: 'graphql',
      TOML: 'ini',
    }

    return languageMap[language] || 'plaintext'
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content || '')
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      console.error('Unable to copy source code.')
    }
  }

  if (!file) {
    return (
      <div className="code-viewer-empty">
        <FileCode2 size={48} />
        <h3>Select a file to view its code</h3>
        <p>Choose any file from the project explorer.</p>
      </div>
    )
  }

  return (
    <div className={`code-viewer ${isFullscreen ? 'fullscreen' : ''}`}>
      <div className="code-viewer-header">
        <div className="code-viewer-file-info">
          <FileCode2 size={18} />

          <div>
            <strong>{file.filename}</strong>
            <span>{file.relative_path}</span>
          </div>
        </div>

        <div className="code-viewer-actions">
          <button
            type="button"
            onClick={handleCopy}
            disabled={isLoading || !!error || !content}
            title="Copy source code"
          >
            {copied ? <Check size={16} /> : <Copy size={16} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <button
            type="button"
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? (
              <Minimize2 size={16} />
            ) : (
              <Maximize2 size={16} />
            )}
          </button>
        </div>
      </div>

      <div className="code-viewer-editor">
        {isLoading ? (
          <div className="code-viewer-message">
            Loading source code...
          </div>
        ) : error ? (
          <div className="code-viewer-message error">
            {error}
          </div>
        ) : (
          <Editor
            height="100%"
            language={getEditorLanguage(file.language)}
            value={content ?? ''}
            theme="vs-dark"
            options={{
              readOnly: true,
              minimap: { enabled: true },
              fontSize: 13,
              fontFamily: 'JetBrains Mono, monospace',
              lineNumbers: 'on',
              scrollBeyondLastLine: false,
              automaticLayout: true,
              wordWrap: 'on',
              padding: { top: 16 },
              renderLineHighlight: 'line',
              folding: true,
            }}
          />
        )}
      </div>
    </div>
  )
}

export default CodeViewer
