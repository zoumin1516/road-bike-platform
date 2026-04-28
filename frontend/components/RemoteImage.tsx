"use client";

import Image, { type ImageProps } from "next/image";
import { type ReactNode, useEffect, useMemo, useState } from "react";

import { isImageCacheAllowed } from "@/lib/image-allowlist";

type RemoteImageProps = Omit<ImageProps, "src" | "onError"> & {
  src?: string | null;
  fallback?: ReactNode;
  fallbackClassName?: string;
};

export function RemoteImage({
  src,
  alt,
  fallback,
  fallbackClassName = "card-image__placeholder",
  ...rest
}: RemoteImageProps) {
  const [errored, setErrored] = useState(false);

  const resolvedSrc = useMemo(() => {
    if (!src || (!src.startsWith("http://") && !src.startsWith("https://"))) {
      return src ?? "";
    }
    if (!isImageCacheAllowed(src)) {
      return src;
    }
    return `/api/image-cache?src=${encodeURIComponent(src)}`;
  }, [src]);

  useEffect(() => {
    setErrored(false);
  }, [src]);

  if (!src) {
    return <div className={fallbackClassName}>{fallback ?? "暂无图卷"}</div>;
  }
  if (errored) {
    return <div className={fallbackClassName}>{fallback ?? "图卷加载失败"}</div>;
  }
  return (
    <Image
      {...rest}
      src={resolvedSrc}
      alt={alt}
      onError={() => setErrored(true)}
    />
  );
}
