interface MetricCardProps {
  label: string
  value: string
  detail: string
  warning?: boolean
}

export function MetricCard({ label, value, detail, warning = false }: MetricCardProps) {
  return (
    <article className={warning ? 'metric-card warning-metric' : 'metric-card'}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  )
}
