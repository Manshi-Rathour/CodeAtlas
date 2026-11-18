import { LoaderCircle } from 'lucide-react'

import './CommonStates.css'

function LoadingSpinner({ label = 'Loading...', compact = false }) {
  return (
    <div className={`loading-state ${compact ? 'compact' : ''}`}>
      <LoaderCircle size={compact ? 20 : 30} className="spin" />
      <span>{label}</span>
    </div>
  )
}

export default LoadingSpinner
