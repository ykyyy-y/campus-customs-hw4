import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import type { Product } from '../types'
import { formatPrice, stockBadge } from './ProductCard'

const ROTATE_MS = 5200

/**
 * Interactive merchandise showcase for the hero.
 *
 * Rotates through a handful of real products, and lets the shopper take over by clicking
 * a thumbnail. The rotation stops the moment they interact or hover, so it never fights
 * the person using it. Each frame links straight to that product's page.
 */
export default function HeroShowcase({ products }: { products: Product[] }) {
  const [index, setIndex] = useState(0)
  const [swapping, setSwapping] = useState(false)
  const [paused, setPaused] = useState(false)
  const timerRef = useRef<number | null>(null)

  const reduceMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  useEffect(() => {
    if (products.length < 2 || paused || reduceMotion) return
    timerRef.current = window.setInterval(() => {
      setSwapping(true)
      window.setTimeout(() => {
        setIndex((current) => (current + 1) % products.length)
        setSwapping(false)
      }, 260)
    }, ROTATE_MS)
    return () => {
      if (timerRef.current !== null) window.clearInterval(timerRef.current)
    }
  }, [products.length, paused, reduceMotion])

  if (products.length === 0) {
    return (
      <div className="showcase">
        <div className="showcase-stage skeleton" style={{ height: 'auto' }} />
      </div>
    )
  }

  const active = products[index]
  const badge = stockBadge(active.total_stock)

  function select(next: number) {
    if (next === index) return
    setPaused(true) // the shopper is driving now
    setSwapping(true)
    window.setTimeout(() => {
      setIndex(next)
      setSwapping(false)
    }, 200)
  }

  return (
    <div
      className="showcase"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <div className="showcase-stage">
        <img
          key={active.product_id}
          className={swapping ? 'swapping' : undefined}
          src={active.image_url}
          alt={active.name}
        />
        <div className="showcase-meta">
          <span className="showcase-type">{active.garment_type}</span>
          <h3>{active.name}</h3>
          <div className="showcase-row">
            <span className="showcase-price">{formatPrice(active.price)}</span>
            <span className={`stock-float ${badge.tone}`} style={{ position: 'static', transform: 'none' }}>
              <i className="live-dot" aria-hidden="true" />
              {badge.label}
            </span>
            <Link className="showcase-cta" to={`/products/${active.product_id}`}>
              View item &rarr;
            </Link>
          </div>
        </div>
      </div>

      <div className="showcase-rail">
        {products.map((product, position) => (
          <button
            key={product.product_id}
            type="button"
            className={position === index ? 'showcase-thumb active' : 'showcase-thumb'}
            onClick={() => select(position)}
            aria-label={`Show ${product.name}`}
            aria-current={position === index}
          >
            <img src={product.image_url} alt="" loading="lazy" />
          </button>
        ))}
      </div>
    </div>
  )
}
