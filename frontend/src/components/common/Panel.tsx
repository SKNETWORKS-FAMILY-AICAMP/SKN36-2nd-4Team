import type { ReactNode } from 'react'

interface PanelProps {
  title: string
  chip?: ReactNode
  chipClassName?: string
  className?: string
  footnote?: ReactNode
  children: ReactNode
}

export function Panel({
  title,
  chip,
  chipClassName,
  className,
  footnote,
  children,
}: PanelProps) {
  return (
    <article className={className ? `panel ${className}` : 'panel'}>
      <div className="panel-title">
        <h2>{title}</h2>
        {chip != null ? (
          <span className={chipClassName ? `panel-chip ${chipClassName}` : 'panel-chip'}>{chip}</span>
        ) : null}
      </div>
      {children}
      {footnote ? <p className="panel-footnote">{footnote}</p> : null}
    </article>
  )
}
