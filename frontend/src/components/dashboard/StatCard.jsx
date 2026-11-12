
function StatCard({ title, value, description, icon: Icon, accent = 'blue' }) {
  return (
    <div className={`stat-card stat-card-${accent}`}>
      <div className="stat-card-top">
        <div className="stat-card-icon">
          <Icon size={21} />
        </div>

        <span className="stat-card-label">
          {title}
        </span>
      </div>

      <div className="stat-card-value">
        {value ?? 0}
      </div>

      <p className="stat-card-description">
        {description}
      </p>
    </div>
  )
}

export default StatCard
