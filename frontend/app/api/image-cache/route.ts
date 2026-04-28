import { getOrFetchCachedImage } from "@/lib/server/image-disk-cache";

export const runtime = "nodejs";

/** 浏览器 / CDN 长期缓存；源图地址不变时 URL（含 src 参数）不变，可安全 immutable */
const BROWSER_CACHE_CONTROL = "public, max-age=31536000, immutable";

/**
 * GET /api/image-cache?src=https%3A%2F%2F...
 * 首次从白名单 CDN 拉取并写入磁盘；之后直接读本地文件。
 */
export async function GET(request: Request): Promise<Response> {
  const url = new URL(request.url);
  const src = url.searchParams.get("src");
  if (!src) {
    return new Response("Missing src", { status: 400 });
  }

  let remote: string;
  try {
    remote = decodeURIComponent(src);
  } catch {
    return new Response("Invalid src encoding", { status: 400 });
  }

  try {
    const { body, contentType } = await getOrFetchCachedImage(remote);
    return new Response(new Uint8Array(body), {
      status: 200,
      headers: {
        "Content-Type": contentType,
        "Cache-Control": BROWSER_CACHE_CONTROL
      }
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Image fetch failed";
    return new Response(message, { status: 502 });
  }
}
