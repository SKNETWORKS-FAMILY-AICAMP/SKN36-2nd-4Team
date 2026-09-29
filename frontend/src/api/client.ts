import type {
  RiskUser,
  RiskUserListResponse,
  ModelMetricsResponse,
  SummaryResponse,
  SyntheticSurvivalResponse,
  UserDetailResponse,
} from './types'
import { syntheticSurvivalFallback } from '../data/syntheticSurvivalFallback'
import { modelMetricsFallback } from '../data/modelMetricsFallback'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`)

  if (!response.ok) {
    throw new Error(`API 요청에 실패했습니다. (${response.status})`)
  }

  return response.json() as Promise<T>
}

export const dashboardApi = {
  getSummary: (gameMode = 'ALL') =>
    request<SummaryResponse>(`/summary?game_mode=${encodeURIComponent(gameMode)}`),
  getModelMetrics: async () => {
    try {
      const response = await request<ModelMetricsResponse>('/model/metrics')
      // 서버가 pending이거나 details가 비어 있어도 페이지 전체를 빈 상태로 바꾸지 않는다.
      return response.model_status === 'ready' && response.details
        ? response
        : modelMetricsFallback
    } catch {
      // 발표/시연 중 API 연결이 끊겨도 커밋된 모델 평가 스냅샷으로 화면을 유지한다.
      return modelMetricsFallback
    }
  },
  getRiskUsers: () => request<RiskUserListResponse>('/risk-users?size=5000'),
  searchUsers: (query: string, limit = 8) =>
    request<RiskUser[]>(
      `/users/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    ),
  getUserDetail: (recordId: string) =>
    request<UserDetailResponse>(`/users/${encodeURIComponent(recordId)}`),
  getMonthlyPositionEda: () => request<{ mode: string; months_available: string[]; items: Array<{ month: string; position: string; matches: number; avg_kda: number; avg_duration_min: number; win_rate: number }> }>('/eda/position-monthly'),
  getSyntheticSurvivalUsers: async () => {
    try {
      return await request<SyntheticSurvivalResponse>('/survival/synthetic-users')
    } catch {
      // 발표/시연 중 백엔드 생존분석 엔드포인트가 일시적으로 5xx를 반환해도
      // 동일 프로젝트 데이터로 만든 로컬 합성 표본을 사용해 화면을 유지한다.
      return syntheticSurvivalFallback
    }
  },
}
