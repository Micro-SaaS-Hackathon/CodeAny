import { mutation, query } from "./_generated/server";

export const upsert = mutation(async (ctx, args: any) => {
  const { db } = ctx;
  const { courseId, moduleId } = args || {};
  if (!courseId || !moduleId) return null;
  const existing = await db
    .query("modules")
    .withIndex("by_course_module", (q: any) => q.eq("courseId", courseId).eq("moduleId", String(moduleId)))
    .unique();

  const doc: any = {
    courseId,
    moduleId: String(moduleId),
    title: args.title,
    outline: args.outline ?? [],
    text: args.text ?? "",
    manimCode: args.manimCode ?? "",
    imageStorageId: args.imageStorageId ?? null,
    imageCaption: args.imageCaption ?? null,
    videoStorageId: args.videoStorageId ?? null,
  };

  if (existing) {
    await db.patch(existing._id, doc);
    return { ok: true, id: String(existing._id) };
  } else {
    const _id = await db.insert("modules", doc);
    return { ok: true, id: String(_id) };
  }
});

export const listByCourse = query(async (ctx, { courseId }: { courseId: string }) => {
  const { db } = ctx;
  if (!courseId) return [] as any[];
  const docs = await db
    .query("modules")
    .withIndex("by_course", (q: any) => q.eq("courseId", courseId))
    .collect();
  return docs.map((d: any) => ({
    courseId: d.courseId,
    moduleId: d.moduleId,
    title: d.title ?? null,
    outline: d.outline ?? [],
    text: d.text ?? "",
    manimCode: d.manimCode ?? "",
    imageStorageId: d.imageStorageId ?? null,
    imageCaption: d.imageCaption ?? null,
    videoStorageId: d.videoStorageId ?? null,
  }));
});

export const delete_ = mutation(async (ctx, { courseId, moduleId }: { courseId: string; moduleId: string }) => {
  const { db } = ctx;
  if (!courseId || !moduleId) return null;
  const existing = await db
    .query("modules")
    .withIndex("by_course_module", (q: any) => q.eq("courseId", courseId).eq("moduleId", String(moduleId)))
    .unique();

  if (!existing) return null;
  await db.delete(existing._id);
  return { deleted: true, courseId, moduleId };
});
