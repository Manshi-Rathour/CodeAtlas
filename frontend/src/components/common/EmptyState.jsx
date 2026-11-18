import './CommonStates.css'

function EmptyState({ icon: Icon, title, message, action }) {
  return (
    <div className="empty-state">
      {Icon && (
        <div className="empty-state-icon">
          <Icon size={28} />
        </div>
      )}

      <h3>{title}</h3>

      {message && <p>{message}</p>}

      {action}
    </div>
  )
}

export default EmptyState
