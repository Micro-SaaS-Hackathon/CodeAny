import { useRuntimeConfig, useSupabaseClient } from '#imports'

export interface DashboardStats {
  total_courses: number
  active_teachers: number
  recent_activity: Array<{ course_id: string; event: string; timestamp: string }>
}

export function useStats() {
  const config = useRuntimeConfig()
  const base = config.public.backendUrl
  const supabase = useSupabaseClient()

  async function authHeaders() {
    try {
      const { data } = await supabase.auth.getSession()
      const token = data.session?.access_token
      if (token) return { Authorization: `Bearer ${token}` }
    } catch (err) {
      console.warn('Failed to resolve Supabase session for stats request', err)
    }
    return {}
  }

  async function getStats(): Promise<DashboardStats> {
    const headers = await authHeaders()
    return await $fetch<DashboardStats>(`${base}/stats`, { headers })
  }

  return { getStats }
}
