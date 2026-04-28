import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";

import { isImageCacheAllowed } from "@/lib/image-allowlist";

const DEFAULT_DIR = ".cache/image-cache";
const FETCH_TIMEOUT_MS = 45_000;

function cacheRoot(): string {
  const fromEnv = process.env.IMAGE_CACHE_DIR?.trim();
  if (fromEnv) {
    return path.isAbsolute(fromEnv)
      ? fromEnv
      : path.join(/* turbopackIgnore: true */ process.cwd(), fromEnv);
  }
  return path.join(/* turbopackIgnore: true */ process.cwd(), DEFAULT_DIR);
}

function urlHash(remoteUrl: string): string {
  return createHash("sha256").update(remoteUrl, "utf8").digest("hex");
}

/** 同一 URL（同一 hash）并发只触发一次上游请求 */
const inflight = new Map<string, Promise<{ body: Buffer; contentType: string }>>();

export async function getOrFetchCachedImage(remoteUrl: string): Promise<{
  body: Buffer;
  contentType: string;
}> {
  if (!isImageCacheAllowed(remoteUrl)) {
    throw new Error("URL not allowed for image cache");
  }

  const root = cacheRoot();
  await mkdir(root, { recursive: true });
  const hash = urlHash(remoteUrl);
  const dataPath = path.join(root, hash);
  const metaPath = path.join(root, `${hash}.meta.json`);

  async function readFromDisk(): Promise<{ body: Buffer; contentType: string }> {
    const [body, metaRaw] = await Promise.all([readFile(dataPath), readFile(metaPath, "utf8")]);
    let contentType = "application/octet-stream";
    try {
      const meta = JSON.parse(metaRaw) as { contentType?: string };
      if (meta.contentType) contentType = meta.contentType;
    } catch {
      /* ignore */
    }
    return { body, contentType };
  }

  if (existsSync(dataPath) && existsSync(metaPath)) {
    return readFromDisk();
  }

  const existing = inflight.get(hash);
  if (existing) {
    return existing;
  }

  const task = (async () => {
    if (existsSync(dataPath) && existsSync(metaPath)) {
      return readFromDisk();
    }

    const response = await fetch(remoteUrl, {
      headers: {
        Accept: "image/*,application/octet-stream;q=0.8",
        "User-Agent": "RoadBikeCodex/1.0 (image-cache)"
      },
      signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
      redirect: "follow",
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error(`Upstream ${response.status} for image`);
    }

    const arrayBuffer = await response.arrayBuffer();
    const body = Buffer.from(arrayBuffer);
    const headerType = response.headers.get("content-type");
    let contentType = headerType?.split(";")[0].trim() || "application/octet-stream";
    if (contentType === "application/octet-stream") {
      const sniffed = sniffImageMime(body);
      if (sniffed) contentType = sniffed;
    }

    const tmpData = `${dataPath}.tmp.${process.pid}`;
    const tmpMeta = `${metaPath}.tmp.${process.pid}`;
    await writeFile(tmpData, body);
    await writeFile(
      tmpMeta,
      JSON.stringify({ contentType, source: remoteUrl }, null, 0),
      "utf8"
    );
    await rename(tmpData, dataPath);
    await rename(tmpMeta, metaPath);

    return { body, contentType };
  })().finally(() => {
    inflight.delete(hash);
  });

  inflight.set(hash, task);
  return task;
}

/** JPEG / PNG / GIF / WebP 魔数（上游未返回 Content-Type 时兜底） */
function sniffImageMime(buf: Buffer): string | null {
  if (buf.length < 12) return null;
  if (buf[0] === 0xff && buf[1] === 0xd8 && buf[2] === 0xff) return "image/jpeg";
  if (buf.slice(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))) {
    return "image/png";
  }
  if (
    buf.slice(0, 6).equals(Buffer.from([0x47, 0x49, 0x46, 0x38, 0x39, 0x61])) ||
    buf.slice(0, 6).equals(Buffer.from([0x47, 0x49, 0x46, 0x38, 0x37, 0x61]))
  ) {
    return "image/gif";
  }
  if (
    buf.slice(0, 4).equals(Buffer.from([0x52, 0x49, 0x46, 0x46])) &&
    buf.slice(8, 12).equals(Buffer.from([0x57, 0x45, 0x42, 0x50]))
  ) {
    return "image/webp";
  }
  return null;
}
