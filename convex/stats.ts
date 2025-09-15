import { query } from "./_generated/server";

function parseDate(s?: string) {
  return s ? Date.parse(s) : 0;
}

export const get = query(async ({ db }, { ownerId }: { ownerId: string }) => {
  if (!ownerId) {
    return {
      total_courses: 0,
      active_teachers: 0,
      recent_activity: [],
    };
  }
  const courses: any[] = await db
    .query("courses")
    .withIndex("by_owner", (q: any) => q.eq("ownerId", ownerId))
    .collect();
  const total = courses.length;
  const sorted = [...courses].sort((a, b) => parseDate(a.updated_at) - parseDate(b.updated_at));
  const recent = sorted.slice(-5);
  return {
    total_courses: total,
    active_teachers: total ? 1 : 0,
    recent_activity: recent.map((c: any) => ({
      course_id: c.id ?? String(c._id),
      event: "updated",
      timestamp: c.updated_at ?? new Date().toISOString(),
    })),
  };
});
