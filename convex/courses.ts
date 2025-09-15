import { mutation, query } from "./_generated/server";

function nowIso() {
  return new Date().toISOString();
}

export const list = query(async (ctx, { ownerId }: { ownerId: string }) => {
  const { db } = ctx;
  if (!ownerId) return [] as any[];
  const docs = await db
    .query("courses")
    .withIndex("by_owner", (q: any) => q.eq("ownerId", ownerId))
    .collect();
  return docs.map((d: any) => ({
    id: d.id ?? String(d._id),
    ownerId: d.ownerId,
    title: d.title,
    progress: d.progress ?? 0,
    created_at: d.created_at ?? nowIso(),
    updated_at: d.updated_at ?? nowIso(),
    status: d.status ?? "draft",
  }));
});

export const get = query(async (ctx, { id, ownerId }: { id: string; ownerId: string }) => {
  const { db } = ctx;
  if (!id || !ownerId) return null;
  const course = await db
    .query("courses")
    .withIndex("by_owner_public_id", (q: any) => q.eq("ownerId", ownerId).eq("id", id))
    .unique();
  if (!course) return null;
  const d: any = course;
  return {
    id: d.id ?? String(d._id),
    ownerId: d.ownerId,
    title: d.title,
    progress: d.progress ?? 0,
    created_at: d.created_at ?? nowIso(),
    updated_at: d.updated_at ?? nowIso(),
    status: d.status ?? "draft",
    // detailed fields if present
    topic: d.topic,
    level: d.level,
    moduleCount: d.moduleCount ?? 0,
    moduleIds: d.moduleIds ?? [],
    description: d.description,
    instructor: d.instructor,
    audience: d.audience,
    levelLabel: d.levelLabel,
    durationWeeks: d.durationWeeks ?? null,
    category: d.category,
    ageRange: d.ageRange,
    language: d.language,
  };
});

export const create = mutation(async (ctx, { title, ownerId }: { title: string; ownerId: string }) => {
  const { db } = ctx;
  if (!ownerId) throw new Error("ownerId required");
  const now = nowIso();
  const base: any = {
    id: "",
    ownerId,
    title: title || "Untitled Course",
    progress: 0,
    created_at: now,
    updated_at: now,
    status: "draft",
  };
  const _id = await db.insert("courses", base);
  const id = String(_id);
  await db.patch(_id, { id });
  return { ...base, id };
});

export const createDetailed = mutation(async (ctx, args: any) => {
  const { db } = ctx;
  if (!args?.ownerId) throw new Error("ownerId required");
  const createdAt = args.createdAt ? new Date(args.createdAt * 1000).toISOString() : nowIso();
  const now = nowIso();
  const doc: any = {
    id: "",
    ownerId: args.ownerId,
    title: args.title || args.topic || "Untitled Course",
    progress: args.progress ?? 0,
    created_at: createdAt,
    updated_at: now,
    status: args.status ?? "creating",
    topic: args.topic,
    level: args.level,
    moduleCount: args.moduleCount ?? 0,
    moduleIds: args.moduleIds ?? [],
    description: args.description,
    instructor: args.instructor,
    audience: args.audience,
    levelLabel: args.levelLabel,
    durationWeeks: args.durationWeeks ?? null,
    category: args.category,
    ageRange: args.ageRange,
    language: args.language,
  };
  const _id = await db.insert("courses", doc);
  const id = String(_id);
  await db.patch(_id, { id });
  return { ...doc, id };
});

export const updateProgress = mutation(
  async (
    ctx,
    { courseId, status, progress, ownerId }: { courseId: string; status?: string; progress?: number; ownerId: string }
  ) => {
    const { db } = ctx;
    if (!ownerId) return null;
    const course = await db
      .query("courses")
      .withIndex("by_owner_public_id", (q: any) => q.eq("ownerId", ownerId).eq("id", courseId))
      .unique();
    if (!course) return null;
    const _id = course._id;
    await db.patch(_id, {
      progress: typeof progress === "number" ? progress : course.progress ?? 0,
      status: status ?? course.status,
      updated_at: nowIso(),
    });
    const d: any = await db.get(_id);
    if (!d) return null;
    return {
      id: d.id ?? String(d._id),
      title: d.title,
      progress: d.progress ?? 0,
      created_at: d.created_at ?? nowIso(),
      updated_at: d.updated_at ?? nowIso(),
      status: d.status ?? "draft",
      ownerId: d.ownerId,
    };
  }
);

export const finalize = mutation(
  async (ctx, { courseId, moduleIds, ownerId }: { courseId: string; moduleIds: string[]; ownerId: string }) => {
    const { db } = ctx;
    if (!ownerId) return null;
    const course = await db
      .query("courses")
      .withIndex("by_owner_public_id", (q: any) => q.eq("ownerId", ownerId).eq("id", courseId))
      .unique();
    if (!course) return null;
    await db.patch(course._id, {
      moduleIds: moduleIds ?? [],
      moduleCount: (moduleIds ?? []).length,
      status: "ready",
      updated_at: nowIso(),
    });
    const d: any = await db.get(course._id);
    if (!d) return null;
    return { id: d.id ?? String(d._id) };
  }
);

export const updateBasic = mutation(
  async (
    ctx,
    args: {
      courseId: string
      ownerId: string
      title?: string
      status?: string
      description?: string
      instructor?: string | null
      audience?: string | null
      levelLabel?: string | null
      durationWeeks?: number | null
      category?: string | null
      ageRange?: string | null
      language?: string | null
    }
  ) => {
    const { db } = ctx;
    const { courseId, ownerId } = args;
    if (!ownerId) return null;
    const course = await db
      .query("courses")
      .withIndex("by_owner_public_id", (q: any) => q.eq("ownerId", ownerId).eq("id", courseId))
      .unique();
    if (!course) return null;
    const patch: any = {
      updated_at: nowIso(),
    };
    for (const k of [
      "title",
      "status",
      "description",
      "instructor",
      "audience",
      "levelLabel",
      "durationWeeks",
      "category",
      "ageRange",
      "language",
    ]) {
      if (k in args) (patch as any)[k] = (args as any)[k];
    }
    await db.patch(course._id, patch);
    const d: any = await db.get(course._id);
    if (!d) return null;
    return {
      id: d.id ?? String(d._id),
      ownerId: d.ownerId,
      title: d.title,
      progress: d.progress ?? 0,
      created_at: d.created_at ?? nowIso(),
      updated_at: d.updated_at ?? nowIso(),
      status: d.status ?? "draft",
      description: d.description,
      instructor: d.instructor,
      audience: d.audience,
      levelLabel: d.levelLabel,
      durationWeeks: d.durationWeeks ?? null,
      category: d.category,
      ageRange: d.ageRange,
      language: d.language,
    };
  }
);

export const delete_ = mutation(
  async (ctx, { courseId, ownerId }: { courseId: string; ownerId: string }) => {
    const { db } = ctx;
    if (!ownerId) return null;
    const course = await db
      .query("courses")
      .withIndex("by_owner_public_id", (q: any) => q.eq("ownerId", ownerId).eq("id", courseId))
      .unique();
    if (!course) return null;
    const _id = course._id;
    await db.delete(_id);
    return { deleted: true, id: courseId };
  }
);

export const adoptOrphans = mutation(async (ctx, { ownerId }: { ownerId: string }) => {
  const { db } = ctx;
  if (!ownerId) return { adopted: 0 };
  const docs = await db.query("courses").collect();
  let adopted = 0;
  for (const doc of docs) {
    if (!doc.ownerId) {
      await db.patch(doc._id, { ownerId });
      adopted += 1;
    }
  }
  return { adopted };
});
