import ReactMarkdown from 'react-markdown'

import './MarkdownViewer.css'

// Generated documentation must never navigate away from the app, so
// links are rendered as plain text and images are dropped.
const markdownComponents = {
  a: ({ children }) => <span className="markdown-link-text">{children}</span>,
  img: () => null,
}

function MarkdownViewer({ content, className = '' }) {
  return (
    <div className={`markdown-viewer ${className}`}>
      <ReactMarkdown components={markdownComponents}>
        {content || ''}
      </ReactMarkdown>
    </div>
  )
}

export default MarkdownViewer
