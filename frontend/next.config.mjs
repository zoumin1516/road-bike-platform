/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    root: process.cwd()
  },
  images: {
    // 远端图片直连，绕开 /_next/image 服务端代理，避免上游 CDN ETIMEDOUT 时整页图裂。
    // 这些 CDN 自身已经按尺寸/格式提供了优化版本（wid=、fmt=webp、thumbs/<size>__resize__ 等），
    // 不再依赖 Next.js 服务端再做一次转换。
    unoptimized: true,
    remotePatterns: [
      { protocol: "https", hostname: "giant-images.giant.com.cn" },
      { protocol: "https", hostname: "giant-images.oss-cn-shanghai.aliyuncs.com" },
      { protocol: "https", hostname: "giant-img.oss-cn-shanghai.aliyuncs.com" },
      { protocol: "https", hostname: "giant-yugou.oss-cn-shanghai.aliyuncs.com" },
      { protocol: "https", hostname: "assets.specialized.com" },
      { protocol: "https", hostname: "1500020361.vod2.myqcloud.com" },
      { protocol: "https", hostname: "pinarello.com" }
    ]
  }
};

export default nextConfig;
