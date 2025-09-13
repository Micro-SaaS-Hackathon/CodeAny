import { useState } from '#imports'

export function useCreateCourseModal() {
  const isOpen = useState<boolean>('createCourseModalOpen', () => false)
  function open() { isOpen.value = true }
  function close() { isOpen.value = false }
  return { isOpen, open, close }
}
