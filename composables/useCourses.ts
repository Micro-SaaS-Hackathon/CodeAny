import { useRuntimeConfig } from '#imports'
import type { Course, CourseDetail, Module } from '~/types/course'

const MIN_POLL_INTERVAL = 6000
const TERMINAL_STATUSES = new Set(['ready', 'published', 'failed', 'stopped', 'error', 'cancelled', 'canceled', 'aborted', 'complete', 'completed'])
const ERROR_STATUSES = new Set(['failed', 'error', 'stopped', 'cancelled', 'canceled', 'aborted'])

function normalizeStatus(status?: string | null): string {
  return String(status || '').trim().toLowerCase()
}

function cloneCourses(rows: Course[]): Course[] {
  return rows.map(row => ({ ...row }))
}

function hasMeaningfulChange(prev: Course[], next: Course[]): boolean {
  if (prev.length !== next.length) return true
  const prevMap = new Map(prev.map(course => [course.id, course]))
  for (const course of next) {
    const existing = prevMap.get(course.id)
    if (!existing) return true
    if ((existing.progress ?? 0) !== (course.progress ?? 0)) return true
    if (normalizeStatus(existing.status) !== normalizeStatus(course.status)) return true
    if ((existing.updated_at || '') !== (course.updated_at || '')) return true
  }
  return false
}

function clampProgress(value: number | undefined): number {
  if (typeof value !== 'number' || Number.isNaN(value)) return 0
  return Math.min(100, Math.max(0, Math.round(value)))
}

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

  async function getCourse(id: string): Promise<CourseDetail> {
    return await $fetch<CourseDetail>(`${base}/courses/${id}`, { method: 'GET' })
  }

  type CourseUpdate = Partial<Pick<CourseDetail, 'title' | 'status' | 'description' | 'instructor' | 'audience' | 'level_label' | 'duration_weeks' | 'category' | 'age_range' | 'language'>>

  async function updateCourse(id: string, payload: CourseUpdate): Promise<CourseDetail> {
    return await $fetch<CourseDetail>(`${base}/courses/${id}`, {
      method: 'PATCH',
      body: payload
    })
  }

  async function listModules(courseId: string): Promise<Module[]> {
    return await $fetch<Module[]>(`${base}/courses/${courseId}/modules`, { method: 'GET' })
  }

  async function getModule(courseId: string, moduleId: string): Promise<Module> {
    return await $fetch<Module>(`${base}/courses/${courseId}/modules/${moduleId}`, { method: 'GET' })
  }

  async function upsertModule(courseId: string, moduleId: string, payload: Partial<Module>): Promise<Module> {
    return await $fetch<Module>(`${base}/courses/${courseId}/modules/${moduleId}`, {
      method: 'PATCH',
      body: payload
    })
  }

  async function getConvexFileUrl(storageId: string): Promise<string | null> {
    try {
      const data = await $fetch<{ url: string }>(`${base}/files/convex-url`, { method: 'GET', query: { storageId } })
      return data?.url || null
    } catch { return null }
  }

  async function recompileModule(courseId: string, moduleId: string): Promise<Module> {
    return await $fetch<Module>(`${base}/courses/${courseId}/modules/${moduleId}/recompile`, { method: 'POST' })
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

  function isCourseInFlight(course: Course): boolean {
    const status = normalizeStatus(course.status)
    if (TERMINAL_STATUSES.has(status)) return false
    return clampProgress(course.progress) < 100
  }

  function isCourseErrored(course: Course): boolean {
    return ERROR_STATUSES.has(normalizeStatus(course.status))
  }

  function courseStatusLabel(course: Course): string {
    const status = normalizeStatus(course.status)
    if (ERROR_STATUSES.has(status)) return 'Stopped'
    if (status === 'ready' || status === 'published') return 'Ready'
    if (status === 'creating') return 'Creating'
    if (status === 'rendering') return 'Rendering'
    if (status === 'uploading') return 'Uploading'
    if (!status) return 'Draft'
    const words = status.replace(/[_-]+/g, ' ').split(' ').filter(Boolean)
    return words.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  }

  function courseStatusColor(course: Course): 'gray' | 'green' | 'red' | 'blue' {
    const status = normalizeStatus(course.status)
    if (ERROR_STATUSES.has(status)) return 'red'
    if (status === 'ready' || status === 'published') return 'green'
    if (status === 'creating' || status === 'rendering' || status === 'uploading') return 'blue'
    return 'gray'
  }

  function watchCourseProgress(intervalMs = MIN_POLL_INTERVAL, onUpdate?: (courses: Course[]) => void) {
    const baseInterval = Math.max(intervalMs, MIN_POLL_INTERVAL)
    let timer: ReturnType<typeof setTimeout> | null = null
    let lastSnapshot: Course[] = []

    const poll = async () => {
      try {
        const list = await listCourses()
        const normalized = Array.isArray(list) ? list : []
        const snapshot = cloneCourses(normalized)
        const shouldUpdate = hasMeaningfulChange(lastSnapshot, snapshot)
        lastSnapshot = snapshot
        if (shouldUpdate) {
          onUpdate?.(cloneCourses(snapshot))
        }
        if (normalized.some(isCourseInFlight)) {
          timer = setTimeout(poll, baseInterval)
        } else {
          timer = null
        }
      } catch (err) {
        timer = setTimeout(poll, baseInterval)
      }
    }

    poll()

    return () => {
      if (timer) clearTimeout(timer)
      timer = null
    }
  }

  return {
    listCourses,
    createCourse,
    createCourseAI,
    fetchCategories,
    watchCourseProgress,
    getCourse,
    updateCourse,
    listModules,
    getModule,
    upsertModule,
    getConvexFileUrl,
    recompileModule,
    isCourseInFlight,
    isCourseErrored,
    courseStatusLabel,
    courseStatusColor,
  }
}
