import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { fetchProduct } from '../api'
import { formatPrice, stockBadge } from '../components/ProductCard'
import type { Product } from '../types'

export default function ProductDetail() {
  const { productId } = useParams<{ productId: string }>()
  const [product, setProduct] = useState<Product | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!productId) return
    setLoading(true)
    setError(null)
    fetchProduct(productId)
      .then(setProduct)
      .catch((cause: Error) => setError(cause.message))
      .finally(() => setLoading(false))
  }, [productId])

  if (loading) {
    return (
      <div className="page">
        <div className="detail">
          <div className="skeleton" style={{ height: 460 }} />
          <div className="skeleton" style={{ height: 360 }} />
        </div>
      </div>
    )
  }

  if (error || !product) {
    return (
      <div className="page state">
        <h2>We could not find that item</h2>
        <p>{error ?? 'It may have sold through or the link may be out of date.'}</p>
        <Link className="btn btn-primary" to="/products">
          Back to the catalogue
        </Link>
      </div>
    )
  }

  const badge = stockBadge(product.total_stock)

  return (
    <div className="page">
      <p className="crumbs">
        <Link to="/">Home</Link> / <Link to="/products">Products</Link> / {product.name}
      </p>

      <div className="detail">
        <div className="detail-image">
          <img src={product.image_url} alt={product.name} />
        </div>

        <div>
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>

          <div className="price-row">
            <span className="price">{formatPrice(product.price)}</span>
            <span className={badge.className}>{badge.label}</span>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-faint)' }}>
              {product.total_stock} in the shop
            </span>
          </div>

          <p className="detail-desc">{product.description}</p>

          <div className="spec-block">
            <h2>Sizes and stock</h2>
            <div className="size-grid">
              {product.inventory.map((item) => {
                const soldOut = item.quantity === 0
                const low = !soldOut && item.quantity <= 3
                return (
                  <div
                    key={item.size}
                    className={`size-tile${soldOut ? ' sold-out' : ''}${low ? ' low' : ''}`}
                  >
                    <strong>{item.size}</strong>
                    <span>
                      {soldOut ? 'Sold out' : low ? `Only ${item.quantity} left` : `${item.quantity} in stock`}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {product.colors.length > 0 && (
            <div className="spec-block">
              <h2>Colours</h2>
              <div className="chip-row">
                {product.colors.map((color) => (
                  <span className="chip" key={color}>
                    {color}
                  </span>
                ))}
              </div>
            </div>
          )}

          {product.search_tags.length > 0 && (
            <div className="spec-block">
              <h2>Also known as</h2>
              <div className="chip-row">
                {product.search_tags.map((tag) => (
                  <span className="chip" key={tag}>
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="spec-block">
            <h2>Item code</h2>
            <p style={{ margin: 0, color: 'var(--text-soft)', fontSize: '0.9rem' }}>
              {product.product_id} &mdash; quote this at the counter at 57 Broadway, or ask
              Bailey in the chat to check another size for you.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
