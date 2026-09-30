import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  description: string
  className?: string
  eyebrow?: string
  leading?: ReactNode
  badges?: ReactNode
}

export function PageHeader({
  title,
  description,
  className,
  eyebrow,
  leading,
  badges,
}: PageHeaderProps) {
  return (
    <header className={className ? `page-header ${className}` : 'page-header'}>
      <div>
        {leading}
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
        <p className="page-description">{description}</p>
      </div>
      {badges ? <div className="header-badges">{badges}</div> : null}
    </header>
  )
}
