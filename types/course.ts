export type CourseStatus = 'draft' | 'published' | string

export interface Course {
  id: string
  owner_id?: string
  title: string
  progress: number // 0-100
  created_at: string // ISO 8601
  updated_at: string // ISO 8601
  status: CourseStatus
}

export interface CourseDetail extends Course {
  description?: string | null
  instructor?: string | null
  audience?: string | null
  level_label?: string | null
  duration_weeks?: number | null
  category?: string | null
  age_range?: string | null
  language?: string | null
  modules: Module[]
}

export interface Module {
  courseId: string
  moduleId: string
  title?: string | null
  outline?: any[]
  text?: string
  manimCode?: string
  imageStorageId?: string | null
  imageCaption?: string | null
  videoStorageId?: string | null
}
