/**
 * 允许通过 /api/image-cache 代理并落盘缓存的远端主机。
 * 与 next.config.mjs 的 remotePatterns 保持一致，防止开放代理被滥用。
 */
export const IMAGE_CACHE_ALLOWLIST = new Set([
  "giant-images.giant.com.cn",
  "giant-images.oss-cn-shanghai.aliyuncs.com",
  "giant-img.oss-cn-shanghai.aliyuncs.com",
  "giant-yugou.oss-cn-shanghai.aliyuncs.com",
  "assets.specialized.com",
  "1500020361.vod2.myqcloud.com",
  "pinarello.com"
]);

export function isImageCacheAllowed(urlString: string): boolean {
  try {
    const url = new URL(urlString);
    return url.protocol === "https:" && IMAGE_CACHE_ALLOWLIST.has(url.hostname);
  } catch {
    return false;
  }
}
