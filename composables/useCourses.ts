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

  return { listCourses, createCourse }
}
