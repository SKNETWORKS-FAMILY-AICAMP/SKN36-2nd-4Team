import type {
  RiskUser,
  RiskUserListResponse,
  SummaryResponse,
  SyntheticSurvivalResponse,
  UserDetailResponse,
} from './types'

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
  getRiskUsers: () => request<RiskUserListResponse>('/risk-users?size=5000'),
  searchUsers: (query: string, limit = 8) =>
    request<RiskUser[]>(
      `/users/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    ),
  getUserDetail: (recordId: string) =>
    request<UserDetailResponse>(`/users/${encodeURIComponent(recordId)}`),
  getMonthlyPositionEda: () => request<{ mode: string; months_available: string[]; items: Array<{ month: string; position: string; matches: number; avg_kda: number; avg_duration_min: number; win_rate: number }> }>('/eda/position-monthly'),
  getSyntheticSurvivalUsers: () => request<SyntheticSurvivalResponse>('/survival/synthetic-users'),
}
