import { serverSupabaseClient } from '#supabase/server'
import { defineEventHandler, readBody, createError, H3Event } from 'h3'

export default defineEventHandler(async (event: H3Event) => {
  try {
    const body = await readBody<{ email?: string }>(event)
    const raw = (body?.email || '').trim().toLowerCase()

    // Basic validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!raw || !emailRegex.test(raw)) {
      throw createError({ statusCode: 400, statusMessage: 'Invalid email address' })
    }

    const supabase = await serverSupabaseClient(event)

    // Upsert into `newsletter_subscribers` with unique constraint on email
    const { error } = await supabase
      .from('newsletter_subscribers')
      .upsert({ email: raw }, { onConflict: 'email' })

    if (error) {
      // If table is missing, provide a helpful hint
      if ((error as any).code === '42P01') {
        throw createError({
          statusCode: 500,
          statusMessage: 'Newsletter table not found. Please create `newsletter_subscribers` with a unique `email` column.'
        })
      }
      throw createError({ statusCode: 500, statusMessage: error.message })
    }

    return { ok: true }
  } catch (err: any) {
    if (err?.statusCode) throw err
    throw createError({ statusCode: 500, statusMessage: 'Unexpected server error' })
  }
})
