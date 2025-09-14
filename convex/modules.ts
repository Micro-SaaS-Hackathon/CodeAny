import { mutation } from "./_generated/server";

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
