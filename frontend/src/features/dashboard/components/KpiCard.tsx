import { Icon, type IconName } from '../../../components/common/Icon'

interface KpiCardProps {
  label: string
  value: string
  icon: IconName
  accent?: 'blue' | 'mint' | 'coral' | 'cyan'
  warning?: boolean
}

export function KpiCard({
  label,
  value,
  icon,
  accent = 'blue',
  warning = false,
}: KpiCardProps) {
  return (
    <article className={`kpi-card ${accent}${warning ? ' warning' : ''}`}>
      <span className="kpi-icon">
        <Icon name={icon} />
      </span>
      <div>
        <p className="kpi-label">{label}</p>
        <p className="kpi-value">{value}</p>
      </div>
    </article>
  )
}
