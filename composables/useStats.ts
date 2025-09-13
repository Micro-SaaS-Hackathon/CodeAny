import { useRuntimeConfig } from '#imports'

export interface DashboardStats {
  total_courses: number
  active_teachers: number
  recent_activity: Array<{ course_id: string; event: string; timestamp: string }>
}

export function useStats() {
  const config = useRuntimeConfig()
  const base = config.public.backendUrl

  async function getStats(): Promise<DashboardStats> {
    return await $fetch<DashboardStats>(`${base}/stats`)
  }

  return { getStats }
}
