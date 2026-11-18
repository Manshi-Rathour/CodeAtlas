import { AlertCircle, RefreshCw } from 'lucide-react'

import './CommonStates.css'

function ErrorMessage({
  title = 'Something went wrong',
  message = 'Please try again.',
  onRetry,
  retryLabel = 'Try Again',
}) {
  return (
    <div className="error-state">
      <AlertCircle size={30} />

      <div>
        <h3>{title}</h3>
        <p>{message}</p>
      </div>

      {onRetry && (
        <button type="button" onClick={onRetry}>
          <RefreshCw size={16} />
          {retryLabel}
        </button>
      )}
    </div>
  )
}

export default ErrorMessage
