import { useCallback, useRef } from 'react'
import type { ReactNode } from 'react'

/** Respect the OS "reduce motion" setting; CSS checks the same query. */
function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

const MAX_DEGREES = 7

/**
 * Pointer-driven 3D tilt.
 *
 * The wrapper owns the CSS `perspective`; this component only writes a transform on its
 * single child and two custom properties (`--mx`, `--my`) that position the specular
 * highlight. Writes happen inside `requestAnimationFrame` so a fast mouse cannot queue
 * more style changes than the browser can paint.
 */
export default function Tilt({
  children,
  className = 'tilt',
}: {
  children: ReactNode
  className?: string
}) {
  const hostRef = useRef<HTMLDivElement>(null)
  const frameRef = useRef<number | null>(null)

  const onPointerMove = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    const host = hostRef.current
    if (!host || prefersReducedMotion()) return

    const bounds = host.getBoundingClientRect()
    const px = (event.clientX - bounds.left) / bounds.width
    const py = (event.clientY - bounds.top) / bounds.height

    if (frameRef.current !== null) cancelAnimationFrame(frameRef.current)
    frameRef.current = requestAnimationFrame(() => {
      const card = host.firstElementChild as HTMLElement | null
      if (!card) return
      const rotateY = (px - 0.5) * 2 * MAX_DEGREES
      const rotateX = (0.5 - py) * 2 * MAX_DEGREES
      card.style.transform = `rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-6px)`
      card.style.setProperty('--mx', `${(px * 100).toFixed(1)}%`)
      card.style.setProperty('--my', `${(py * 100).toFixed(1)}%`)
    })
  }, [])

  const reset = useCallback(() => {
    if (frameRef.current !== null) {
      cancelAnimationFrame(frameRef.current)
      frameRef.current = null
    }
    const card = hostRef.current?.firstElementChild as HTMLElement | null
    if (card) card.style.transform = ''
  }, [])

  return (
    <div
      ref={hostRef}
      className={className}
      onPointerMove={onPointerMove}
      onPointerLeave={reset}
      onBlur={reset}
    >
      {children}
    </div>
  )
}
