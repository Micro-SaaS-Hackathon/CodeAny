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
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error('Network response was not ok ' + response.statusText)
      }
      const data = await response.json()
      
      // Extract categories from the CSV resource
      const csvResource = data?.result?.resources?.find((r: any) => r.format === 'CSV')
      if (csvResource?.url) {
        // Fetch the CSV data
        const csvResponse = await fetch(csvResource.url)
        const csvText = await csvResponse.text()
        
        // Parse CSV and extract unique specializations
        const lines = csvText.split('\n').slice(1) // Skip header
        const categories = new Set<string>()
        
        lines.forEach(line => {
          const columns = line.split(',')
          if (columns.length > 1 && columns[1]?.trim()) {
            categories.add(columns[1].trim().replace(/"/g, ''))
          }
        })
        
        return Array.from(categories)
          .filter(Boolean)
          .sort()
          .map(cat => ({ label: cat, value: cat }))
      }
      
      // Fallback to basic categories if CSV parsing fails
      return [
        { label: 'Computer Science', value: 'computer-science' },
        { label: 'Mathematics', value: 'mathematics' },
        { label: 'Engineering', value: 'engineering' },
        { label: 'Business', value: 'business' },
        { label: 'Arts & Humanities', value: 'arts-humanities' },
        { label: 'Natural Sciences', value: 'natural-sciences' },
        { label: 'Social Sciences', value: 'social-sciences' },
        { label: 'Medicine & Health', value: 'medicine-health' }
      ]
    } catch (err) {
      console.error('Error fetching categories:', err)
      // Return fallback categories
      return [
        { label: 'Computer Science', value: 'computer-science' },
        { label: 'Mathematics', value: 'mathematics' },
        { label: 'Engineering', value: 'engineering' },
        { label: 'Business', value: 'business' },
        { label: 'Arts & Humanities', value: 'arts-humanities' },
        { label: 'Natural Sciences', value: 'natural-sciences' },
        { label: 'Social Sciences', value: 'social-sciences' },
        { label: 'Medicine & Health', value: 'medicine-health' }
      ]
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
