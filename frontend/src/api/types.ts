export type ModelStatus = 'pending' | 'ready' | 'error'

export interface SummaryKpis {
  total_users: number
  model_eligible_users: number
  actual_churn_users: number
  actual_churn_rate: number
  unique_matches: number
}

export interface ChurnRatePoint {
  label: string
  rate: number
}

export interface SummaryResponse {
  cutoff_date: string
  collection_scope: string
  model_status: ModelStatus
  kpis: SummaryKpis
  inactivity_churn_rates: ChurnRatePoint[]
  activity_churn_rates: ChurnRatePoint[]
  data_quality_notes: string[]
}

export type RiskLevel = 'HIGH' | 'MEDIUM' | 'LOW'

export interface RiskUser {
  record_id: string
  player_id: string
  risk_score: number
  risk_level: RiskLevel
  last_game_days: number
  recent_matches: number
  win_rate: number
  main_reason: string
}

export interface RiskOverview {
  total_users: number
  high_risk_users: number
  average_score: number
  campaign_target_users: number
  average_inactive_days: number
}

export interface RiskDistributionPoint {
  label: RiskLevel
  count: number
}

export interface RiskUserListResponse {
  items: RiskUser[]
  page: number
  size: number
  total: number
  model_status: ModelStatus
  demo: boolean
  overview: RiskOverview
  distribution: RiskDistributionPoint[]
  message?: string | null
}

export interface ActivityPoint {
  date: string
  matches: number
}

export interface PerformancePoint {
  match_no: number
  kda: number
  win: number
  damage: number
  cs: number
  vision: number
  duration_minutes: number
}

export interface IntervalPoint {
  label: string
  days: number
}

export interface ModePoint {
  mode: string
  count: number
}

export interface RiskReason {
  feature: string
  label: string
  contribution: number
  direction: 'increase' | 'decrease'
}

export interface UserDetailResponse {
  record_id: string
  player_id: string
  risk_score: number
  risk_level: RiskLevel
  last_game_days: number
  recent_matches: number
  recent_win_rate: number
  average_kda: number
  average_interval_days: number
  model_status: ModelStatus
  demo: boolean
  activity: ActivityPoint[]
  performance: PerformancePoint[]
  intervals: IntervalPoint[]
  modes: ModePoint[]
  reasons: RiskReason[]
}

export interface SyntheticSurvivalUser {
  record_id: string
  player_id: string
  risk_band: '고위험' | '주의' | '일반 관찰'
  risk_rank: number
  event_risk_7d: number
  event_risk_14d: number
  event_risk_30d: number
  activity_survival_7d: number
  activity_survival_14d: number
  activity_survival_30d: number
}

export interface SyntheticSurvivalResponse {
  demo: boolean
  cutoff_date: string
  cohort_users: number
  test_users: number
  c_index: number
  risk_band_definition: string
  warning: string
  items: SyntheticSurvivalUser[]
}
