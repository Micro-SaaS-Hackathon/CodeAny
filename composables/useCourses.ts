import { useRuntimeConfig } from '#imports'
import type { Course } from '~/types/course'

export function useCourses() {
  const config = useRuntimeConfig()
  const base = config.public.backendUrl

  async function listCourses(): Promise<Course[]> {
    return await $fetch<Course[]>(`${base}/courses`)
  }

  async function createCourse(title: string = 'Untitled Course'): Promise<Course> {
    return await $fetch<Course>(`${base}/courses`, {
      method: 'POST',
      body: { title }
    })
  }

  return { listCourses, createCourse }
}
