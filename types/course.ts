export type CourseStatus = 'draft' | 'published' | string

export interface Course {
  id: string
  title: string
  progress: number // 0-100
  created_at: string // ISO 8601
  updated_at: string // ISO 8601
  status: CourseStatus
}
