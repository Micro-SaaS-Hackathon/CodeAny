import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  courses: defineTable({
    id: v.string(),
    ownerId: v.optional(v.string()),
    title: v.string(),
    progress: v.number(),
    created_at: v.string(),
    updated_at: v.string(),
    status: v.string(),
    // Detailed/AI fields (optional)
    topic: v.optional(v.string()),
    level: v.optional(v.string()),
    moduleCount: v.optional(v.number()),
    moduleIds: v.optional(v.array(v.string())),
    description: v.optional(v.string()),
    instructor: v.optional(v.string()),
    audience: v.optional(v.string()),
    levelLabel: v.optional(v.string()),
    durationWeeks: v.optional(v.union(v.number(), v.null())),
    category: v.optional(v.string()),
    ageRange: v.optional(v.string()),
    language: v.optional(v.string()),
  })
    .index("by_public_id", ["id"])
    .index("by_owner", ["ownerId"])
    .index("by_owner_public_id", ["ownerId", "id"]),

  modules: defineTable({
    courseId: v.string(),
    moduleId: v.string(),
    title: v.optional(v.string()),
    outline: v.optional(v.array(v.any())),
    text: v.optional(v.string()),
    manimCode: v.optional(v.string()),
    imageStorageId: v.optional(v.union(v.string(), v.null())),
    imageCaption: v.optional(v.union(v.string(), v.null())),
    videoStorageId: v.optional(v.union(v.string(), v.null())),
  })
    .index("by_course", ["courseId"]) 
    .index("by_course_module", ["courseId", "moduleId"]),
});
