import { action } from "./_generated/server";

export const generateUploadUrl = action(async (ctx) => {
  const url = await ctx.storage.generateUploadUrl();
  return url;
});
