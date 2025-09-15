import { action } from "./_generated/server";

export const generateUploadUrl = action(async (ctx) => {
  const url = await ctx.storage.generateUploadUrl();
  return url;
});

export const getUrl = action(async (ctx, args: { storageId: string }) => {
  const { storageId } = args || ({} as any);
  if (!storageId) return null as any;
  const url = await ctx.storage.getUrl(storageId as any);
  return url;
});
