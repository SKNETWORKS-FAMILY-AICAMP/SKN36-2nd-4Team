export type ModelStatus = 'pending' | 'ready' | 'error'

export interface RankingCutoffMetrics {
  selected: number
  found_churn: number
  false_alarms: number
  precision: number
  recall: number
  f1: number
}

export interface CohortModelMetrics {
  users: number
  churners: number
  prevalence: number
  pr_auc_ap: number
  roc_auc: number
  top_10pct: RankingCutoffMetrics
  top_20pct: RankingCutoffMetrics
}

export interface CandidateModelRow {
  feature_set: string
  treatment: string
  ap: string
  roc_auc: string
  recall_10: string
  precision_10: string
  f1_10: string
  recall_20: string
  precision_20: string
  f1_20: string
  found_20: string
  false_alarms_20: string
}

export interface BoostingComparisonRow {
  model: string
  users: string
  churners: string
  pr_auc_ap: string
  roc_auc: string
  recall_10: string
  precision_10: string
  recall_20: string
  precision_20: string
  f1_20: string
  found_20: string
  false_alarms_20: string
}

export interface ModelExperimentDetails {
  model_version: string
  selected_candidate: { feature_set: string; treatment: string }
  nested_selection_oof: Record<string, CohortModelMetrics>
  selected_candidate_oof_exploratory: Record<string, CohortModelMetrics>
  candidates: CandidateModelRow[]
  boosting_comparison: BoostingComparisonRow[]
  boosting_comparison_manifest: {
    cutoff?: string
    users: number
    churners: number
    features?: string[]
    feature_count: number
    models?: string[]
    folds: number
    seed?: number
    split?: string
    imputation?: string
    imbalance?: string
    hyperparameters?: string
    limitations: string[]
  }
  selected_model_shap: Array<{ feature: string; mean_abs_shap: string }>
  selected_features: string[]
  feature_engineering: {
    source_aggregate_features: string[]
    engineered_features: string[]
    uses_only_pre_cutoff_features?: boolean
  }
  limitations: string[]
}

export interface ModelMetricsResponse {
  model_status: ModelStatus
  model_version: string | null
  metrics: Record<string, number>
  message: string | null
  details: ModelExperimentDetails | null
}

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

export interface TierObservation {
  tier: string
  users: number
  churners: number
  observed_no_match_rate: number
  average_win_rate: number | null
  win_rate_n: number
  average_kda: number | null
  kda_n: number
  average_games_30d: number | null
  games_30d_n: number
}

export interface TierAnalysis {
  core_users: number
  matched_users: number
  unmatched_users: number
  tier_source: string
  tier_collection_time_known: boolean
  tiers: TierObservation[]
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
  tier_analysis: TierAnalysis | null
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
