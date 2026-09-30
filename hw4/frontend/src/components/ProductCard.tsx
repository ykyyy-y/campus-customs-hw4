import { Link } from 'react-router-dom'

import type { Product } from '../types'
import Tilt from './Tilt'

/** Turns raw stock into the badge a shopper actually understands. */
export function stockBadge(totalStock: number) {
  if (totalStock === 0) return { className: 'pill pill-out', label: 'Sold out', tone: 'out' }
  if (totalStock <= 10)
    return { className: 'pill pill-low', label: `Only ${totalStock} left`, tone: 'low' }
  return { className: 'pill pill-ok', label: 'In stock', tone: 'ok' }
}

export function formatPrice(price: number) {
  return `$${price.toFixed(2)}`
}

/** Shorten the catalogue description to a card-sized blurb without cutting mid-word. */
function shorten(text: string, maxLength = 96) {
  if (text.length <= maxLength) return text
  const cut = text.slice(0, maxLength)
  return `${cut.slice(0, cut.lastIndexOf(' '))}...`
}

/**
 * The whole card is the link, so clicking anywhere opens the single-item page.
 *
 * One component renders cards everywhere they appear: the catalogue grid, the home page,
 * the chat panel, and the chat-results strip. That is why a card Bailey put on the page
 * behaves exactly like a catalogue card - same route, same detail view - with no extra
 * wiring. `compact` only changes spacing, never behaviour.
 */
export default function ProductCard({
  product,
  compact = false,
  onNavigate,
}: {
  product: Product
  compact?: boolean
  onNavigate?: () => void
}) {
  const badge = stockBadge(product.total_stock)

  return (
    <Tilt>
      <Link
        className={compact ? 'product-card compact' : 'product-card'}
        to={`/products/${product.product_id}`}
        onClick={onNavigate}
      >
        <div className="thumb">
          {/* Floating availability badge, lifted off the card in 3D. The dot pulses
              while stock is healthy and beats faster when it is running out. */}
          <span className={`stock-float ${badge.tone}`}>
            <i className="live-dot" aria-hidden="true" />
            {badge.label}
          </span>
          <img src={product.image_url} alt={product.name} loading="lazy" />
        </div>
        <div className="body">
          <span className="type">{product.garment_type}</span>
          <h3>{product.name}</h3>
          <p className="blurb">{shorten(product.description, compact ? 64 : 96)}</p>
          <div className="foot">
            <span className="price">{formatPrice(product.price)}</span>
            <span className="quick-view">Quick view &rarr;</span>
          </div>
        </div>
      </Link>
    </Tilt>
  )
}
