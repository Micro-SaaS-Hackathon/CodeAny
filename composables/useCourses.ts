import { useRuntimeConfig } from '#imports'
import type { Course } from '~/types/course'

export function useCourses() {
  const config = useRuntimeConfig()
  const base = config.public.backendUrl

  async function listCourses(): Promise<Course[]> {
    const data = await $fetch<any>(`${base}/courses`, { method: 'GET' })
    // Normalize to an array of Course
    if (Array.isArray(data)) return data as Course[]
    if (data && Array.isArray((data as any).items)) return (data as any).items as Course[]
    return []
  }

  async function createCourse(title: string = 'Untitled Course'): Promise<Course> {
    return await $fetch<Course>(`${base}/courses`, {
      method: 'POST',
      body: { title }
    })
  }

  type AICourseRequest = {
    topic: string
    level?: 'beginner' | 'intermediate' | 'advanced' | string
    title: string
    description: string
    instructor?: string | null
    audience?: string | null
    level_label?: string | null
    duration_weeks?: number | null
    category?: string | null
    age_range?: string | null
    language?: 'en' | 'az'
    learning_outcomes?: string[]
    prerequisites?: string[]
    constraints?: Record<string, any>
  }

  async function createCourseAI(payload: AICourseRequest): Promise<{ thread_id: string; course: any }> {
    return await $fetch(`${base}/ai/build`, {
      method: 'POST',
      body: payload
    }) as any
  }

  async function fetchCategories(): Promise<{ label: string; value: string }[]> {
    const url = 'https://admin.opendata.az/api/3/action/package_show?id=bakalavriat-seviyyesi-uzre-ixtisaslar'
    try {
      const data = await fetch(url).then(r => { if (!r.ok) throw new Error('Network response was not ok ' + r.statusText); return r.json() })
      const items: any[] = data?.result?.resources || []
      return items.map((r: any) => ({ label: r.name || r.id, value: r.id }))
    } catch (err) {
      console.error('Error fetching categories:', err)
      return []
    }
  }

  function watchCourseProgress(intervalMs = 4000, onUpdate?: (courses: Course[]) => void) {
    let timer: any
    const start = async () => {
      try {
        const list = await listCourses()
        onUpdate?.(list)
      } catch {}
      timer = setTimeout(start, intervalMs)
    }
    start()
    return () => { if (timer) clearTimeout(timer) }
  }

  return { listCourses, createCourse, createCourseAI, fetchCategories, watchCourseProgress }
}
