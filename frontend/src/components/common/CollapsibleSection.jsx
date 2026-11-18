import { ChevronDown } from 'lucide-react'

import './CollapsibleSection.css'

function CollapsibleSection({
  icon: Icon,
  title,
  subtitle,
  meta,
  headingLevel = 'h2',
  className = '',
  children,
}) {
  const Heading = headingLevel

  return (
    <details className={`collapsible-section ${className}`.trim()}>
      <summary className="collapsible-summary">
        <div className="collapsible-heading">
          {Icon && <Icon size={18} />}

          <div>
            <Heading>{title}</Heading>
            {subtitle && <p>{subtitle}</p>}
          </div>
        </div>

        <span className="collapsible-side">
          {meta !== undefined && meta !== null && meta !== '' && (
            <b className="collapsible-meta">{meta}</b>
          )}

          <ChevronDown size={17} className="collapsible-chevron" />
        </span>
      </summary>

      <div className="collapsible-body">{children}</div>
    </details>
  )
}

export default CollapsibleSection
