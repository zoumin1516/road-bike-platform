"use client";

import {
  type CSSProperties,
  type PointerEvent as ReactPointerEvent,
  type WheelEvent as ReactWheelEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";

import { RemoteImage } from "@/components/RemoteImage";

export type GalleryImage = {
  id: number | string;
  image_url: string;
  alt?: string;
};

type BikeGalleryProps = {
  images: GalleryImage[];
  alt: string;
};

const MIN_SCALE = 1;
const MAX_SCALE = 4;
const SCALE_STEP = 0.4;

export function BikeGallery({ images, alt }: BikeGalleryProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [lightboxOpen, setLightboxOpen] = useState(false);

  const dragStateRef = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    originX: number;
    originY: number;
  } | null>(null);

  const total = images.length;
  const activeImage = images[activeIndex];

  const resetTransform = useCallback(() => {
    setScale(1);
    setOffset({ x: 0, y: 0 });
  }, []);

  const goTo = useCallback(
    (index: number) => {
      if (total === 0) return;
      const next = ((index % total) + total) % total;
      setActiveIndex(next);
      resetTransform();
    },
    [total, resetTransform]
  );

  const handlePrev = useCallback(() => goTo(activeIndex - 1), [goTo, activeIndex]);
  const handleNext = useCallback(() => goTo(activeIndex + 1), [goTo, activeIndex]);

  const zoomBy = useCallback((delta: number) => {
    setScale((prev) => {
      const next = clamp(prev + delta, MIN_SCALE, MAX_SCALE);
      if (next === MIN_SCALE) {
        setOffset({ x: 0, y: 0 });
      }
      return next;
    });
  }, []);

  const handleWheel = useCallback(
    (event: ReactWheelEvent<HTMLDivElement>) => {
      if (!activeImage) return;
      event.preventDefault();
      const delta = event.deltaY < 0 ? SCALE_STEP : -SCALE_STEP;
      zoomBy(delta);
    },
    [zoomBy, activeImage]
  );

  const handlePointerDown = useCallback(
    (event: ReactPointerEvent<HTMLDivElement>) => {
      if (scale <= MIN_SCALE) return;
      event.currentTarget.setPointerCapture(event.pointerId);
      dragStateRef.current = {
        pointerId: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
        originX: offset.x,
        originY: offset.y
      };
      setIsDragging(true);
    },
    [scale, offset]
  );

  const handlePointerMove = useCallback((event: ReactPointerEvent<HTMLDivElement>) => {
    const drag = dragStateRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    const dx = event.clientX - drag.startX;
    const dy = event.clientY - drag.startY;
    setOffset({ x: drag.originX + dx, y: drag.originY + dy });
  }, []);

  const handlePointerEnd = useCallback((event: ReactPointerEvent<HTMLDivElement>) => {
    const drag = dragStateRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    event.currentTarget.releasePointerCapture(event.pointerId);
    dragStateRef.current = null;
    setIsDragging(false);
  }, []);

  const handleDoubleClick = useCallback(() => {
    setScale((prev) => {
      if (prev > MIN_SCALE) {
        setOffset({ x: 0, y: 0 });
        return MIN_SCALE;
      }
      return 2;
    });
  }, []);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (lightboxOpen && event.key === "Escape") {
        setLightboxOpen(false);
        resetTransform();
        return;
      }
      if (event.key === "ArrowLeft") handlePrev();
      else if (event.key === "ArrowRight") handleNext();
      else if (event.key === "+" || event.key === "=") zoomBy(SCALE_STEP);
      else if (event.key === "-" || event.key === "_") zoomBy(-SCALE_STEP);
      else if (event.key === "0") resetTransform();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handlePrev, handleNext, zoomBy, resetTransform, lightboxOpen]);

  useEffect(() => {
    if (!lightboxOpen) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [lightboxOpen]);

  const transformStyle = useMemo<CSSProperties>(
    () => ({
      transform: `translate3d(${offset.x}px, ${offset.y}px, 0) scale(${scale})`,
      cursor: scale > MIN_SCALE ? (isDragging ? "grabbing" : "grab") : "zoom-in",
      transition: isDragging ? "none" : "transform 0.18s ease-out"
    }),
    [offset, scale, isDragging]
  );

  if (total === 0 || !activeImage) {
    return (
      <section className="gallery">
        <div className="gallery-stage">
          <div className="card-image__placeholder">暂无图卷</div>
        </div>
      </section>
    );
  }

  return (
    <section className="gallery">
      <div className="gallery-stage">
        <div
          className="gallery-viewport"
          onWheel={handleWheel}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerEnd}
          onPointerCancel={handlePointerEnd}
          onPointerLeave={handlePointerEnd}
          onDoubleClick={handleDoubleClick}
          role="presentation"
        >
          <div className="gallery-stage__image" style={transformStyle}>
            <RemoteImage
              src={activeImage.image_url}
              alt={activeImage.alt || alt}
              width={1600}
              height={1100}
              priority
              draggable={false}
              style={{ width: "100%", height: "auto", objectFit: "contain", userSelect: "none" }}
              fallbackClassName="card-image__placeholder gallery-fallback"
            />
          </div>
        </div>

        <div className="gallery-controls">
          <button
            type="button"
            className="gallery-btn"
            onClick={() => zoomBy(-SCALE_STEP)}
            disabled={scale <= MIN_SCALE}
            aria-label="缩小"
          >
            <span aria-hidden>−</span>
          </button>
          <span className="gallery-scale" aria-live="polite">
            {(scale * 100).toFixed(0)}%
          </span>
          <button
            type="button"
            className="gallery-btn"
            onClick={() => zoomBy(SCALE_STEP)}
            disabled={scale >= MAX_SCALE}
            aria-label="放大"
          >
            <span aria-hidden>+</span>
          </button>
          <button
            type="button"
            className="gallery-btn"
            onClick={resetTransform}
            disabled={scale === MIN_SCALE && offset.x === 0 && offset.y === 0}
            aria-label="重置"
          >
            <span aria-hidden>⤺</span>
          </button>
          <button
            type="button"
            className="gallery-btn"
            onClick={() => {
              resetTransform();
              setLightboxOpen(true);
            }}
            aria-label="全屏"
          >
            <span aria-hidden>⛶</span>
          </button>
        </div>

        {total > 1 ? (
          <>
            <button
              type="button"
              className="gallery-nav gallery-nav--prev"
              onClick={handlePrev}
              aria-label="上一张图片"
            >
              <span aria-hidden>‹</span>
            </button>
            <button
              type="button"
              className="gallery-nav gallery-nav--next"
              onClick={handleNext}
              aria-label="下一张图片"
            >
              <span aria-hidden>›</span>
            </button>
            <div className="gallery-counter">
              {activeIndex + 1} / {total}
            </div>
          </>
        ) : null}
      </div>

      {total > 1 ? (
        <div className="gallery-thumbs gallery-thumbs--list" role="tablist">
          {images.map((image, index) => (
            <button
              key={image.id}
              type="button"
              role="tab"
              aria-selected={index === activeIndex}
              className={`gallery-thumb ${index === activeIndex ? "is-active" : ""}`}
              onClick={() => goTo(index)}
            >
              <RemoteImage
                src={image.image_url}
                alt={image.alt || `${alt} ${index + 1}`}
                width={240}
                height={160}
                style={{ width: "100%", height: "100%", objectFit: "contain" }}
                fallbackClassName="card-image__placeholder gallery-fallback gallery-fallback--thumb"
              />
            </button>
          ))}
        </div>
      ) : null}

      {lightboxOpen ? (
        <div
          className="gallery-lightbox"
          role="dialog"
          aria-modal="true"
          aria-label={`${alt} 全屏画廊`}
          onClick={(event) => {
            if (event.target === event.currentTarget) {
              setLightboxOpen(false);
              resetTransform();
            }
          }}
        >
          <button
            type="button"
            className="gallery-btn gallery-lightbox__close"
            aria-label="关闭"
            onClick={() => {
              setLightboxOpen(false);
              resetTransform();
            }}
          >
            <span aria-hidden>×</span>
          </button>
          <div
            className="gallery-lightbox__viewport"
            onWheel={handleWheel}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerEnd}
            onPointerCancel={handlePointerEnd}
            onPointerLeave={handlePointerEnd}
            onDoubleClick={handleDoubleClick}
          >
            <div className="gallery-lightbox__image" style={transformStyle}>
              <RemoteImage
                src={activeImage.image_url}
                alt={activeImage.alt || alt}
                width={2400}
                height={1600}
                draggable={false}
                style={{ maxWidth: "92vw", maxHeight: "82vh", width: "auto", height: "auto", objectFit: "contain", userSelect: "none" }}
                fallbackClassName="card-image__placeholder gallery-fallback gallery-fallback--lightbox"
              />
            </div>
          </div>
          {total > 1 ? (
            <>
              <button
                type="button"
                className="gallery-nav gallery-nav--prev gallery-nav--lightbox"
                onClick={handlePrev}
                aria-label="上一张图片"
              >
                <span aria-hidden>‹</span>
              </button>
              <button
                type="button"
                className="gallery-nav gallery-nav--next gallery-nav--lightbox"
                onClick={handleNext}
                aria-label="下一张图片"
              >
                <span aria-hidden>›</span>
              </button>
              <div className="gallery-counter gallery-counter--lightbox">
                {activeIndex + 1} / {total}
              </div>
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}
