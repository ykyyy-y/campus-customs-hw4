import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { fetchGarmentTypes, fetchProducts } from '../api'
import { useChatResults } from '../chatResults'
import ProductCard from '../components/ProductCard'
import type { Product } from '../types'

const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
type Sort = 'name' | 'price-asc' | 'price-desc'

export default function Products() {
  const { products: chatMatches, query: chatQuery, clear: clearChatMatches } = useChatResults()

  // Filters live in the URL, so Back steps through filter changes and a filtered view
  // can be bookmarked or sent to someone.
  const [params, setParams] = useSearchParams()
  const search = params.get('search') ?? ''
  const garmentType = params.get('type') ?? ''
  const size = params.get('size') ?? ''
  const inStockOnly = params.get('stock') === 'in'
  const sort = (params.get('sort') as Sort) ?? 'name'

  const [products, setProducts] = useState<Product[]>([])
  const [garmentTypes, setGarmentTypes] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function update(changes: Record<string, string | null>) {
    const next = new URLSearchParams(params)
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value)
      else next.delete(key)
    }
    setParams(next, { replace: false })
  }

  useEffect(() => {
    fetchGarmentTypes()
      .then(setGarmentTypes)
      .catch(() => undefined)
  }, [])

  // Debounced so typing in the search box does not fire a request per keystroke.
  useEffect(() => {
    setLoading(true)
    const timer = setTimeout(() => {
      fetchProducts({ search, garmentType })
        .then((rows) => {
          setProducts(rows)
          setError(null)
        })
        .catch((cause: Error) => setError(cause.message))
        .finally(() => setLoading(false))
    }, 220)
    return () => clearTimeout(timer)
  }, [search, garmentType])

  const visible = useMemo(() => {
    let rows = [...products]

    // `sizes_in_stock` comes from the inventory table, so picking L hides products whose
    // L row is at zero - not just products that never come in L.
    if (size) rows = rows.filter((product) => product.sizes_in_stock.includes(size))
    if (inStockOnly) rows = rows.filter((product) => product.total_stock > 0)

    if (sort === 'price-asc') rows.sort((a, b) => a.price - b.price)
    if (sort === 'price-desc') rows.sort((a, b) => b.price - a.price)
    return rows
  }, [products, size, inStockOnly, sort])

  // `size` is stated separately in the summary sentence, so it is not repeated here.
  const activeFilters = [
    search && `“${search}”`,
    garmentType,
    inStockOnly && 'in stock only',
  ].filter(Boolean) as string[]

  const hasFilters = activeFilters.length > 0 || Boolean(size)

  return (
    <div className="page">
      <p className="eyebrow">The catalogue</p>
      <h1>Everything on the racks</h1>
      <p className="lede">
        Hoodies, crewnecks, quarter-zips and tees, all officially licensed and all in stock
        on Broadway. Click any item to see the full description and what we have left in
        each size.
      </p>

      <div className="filters" style={{ marginTop: '2rem' }}>
        <div className="field">
          <label htmlFor="search">Search</label>
          <input
            id="search"
            className="control"
            value={search}
            onChange={(event) => update({ search: event.target.value })}
            placeholder="hoodie, Branford, navy, The Game..."
          />
        </div>
        <div className="field">
          <label htmlFor="type">Garment</label>
          <select
            id="type"
            className="control"
            value={garmentType}
            onChange={(event) => update({ type: event.target.value })}
          >
            <option value="">All garments</option>
            {garmentTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="sort">Sort</label>
          <select
            id="sort"
            className="control"
            style={{ minWidth: 170 }}
            value={sort}
            onChange={(event) => update({ sort: event.target.value })}
          >
            <option value="name">A to Z</option>
            <option value="price-asc">Price: low to high</option>
            <option value="price-desc">Price: high to low</option>
          </select>
        </div>

        <div className="field size-field">
          <label>Your size</label>
          <div className="size-chips" role="group" aria-label="Filter by size in stock">
            {SIZES.map((option) => (
              <button
                key={option}
                type="button"
                className={option === size ? 'size-chip active' : 'size-chip'}
                aria-pressed={option === size}
                onClick={() => update({ size: option === size ? null : option })}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <label className="stock-toggle">
          <input
            type="checkbox"
            checked={inStockOnly}
            onChange={(event) => update({ stock: event.target.checked ? 'in' : null })}
          />
          In stock only
        </label>

        <span className="result-count">
          {loading ? 'Loading...' : `${visible.length} item${visible.length === 1 ? '' : 's'}`}
        </span>
      </div>

      {hasFilters && (
        <p className="filter-summary">
          Showing{' '}
          {size ? (
            <>
              only what we have in <strong>size {size}</strong>
            </>
          ) : (
            'the whole catalogue'
          )}
          {activeFilters.length > 0 && <> &middot; {activeFilters.join(' · ')}</>}
          <button className="link-button" onClick={() => setParams(new URLSearchParams())}>
            Clear all
          </button>
        </p>
      )}

      {chatMatches.length > 0 && (
        <section className="chat-matches">
          <div className="section-head">
            <div>
              <p className="eyebrow">&#128054; Bailey found these for you</p>
              <h2>
                {chatMatches.length} match{chatMatches.length === 1 ? '' : 'es'}
                {chatQuery ? ` for “${chatQuery}”` : ''}
              </h2>
            </div>
            <button className="btn btn-ghost" onClick={clearChatMatches}>
              Clear
            </button>
          </div>
          <div className="product-grid">
            {chatMatches.map((product) => (
              <ProductCard key={product.product_id} product={product} />
            ))}
          </div>
        </section>
      )}

      {error && <div className="notice">{error}</div>}

      {loading ? (
        <div className="skeleton-grid">
          {Array.from({ length: 8 }, (_, index) => (
            <div className="skeleton" key={index} />
          ))}
        </div>
      ) : visible.length === 0 ? (
        <div className="state">
          <h2>Nothing matched that</h2>
          <p>
            {size
              ? `We have nothing in size ${size} for those filters. Try another size, or clear the filters.`
              : 'Try a broader word, or clear the garment filter to see the whole catalogue.'}
          </p>
          <button className="btn btn-primary" onClick={() => setParams(new URLSearchParams())}>
            Clear all filters
          </button>
        </div>
      ) : (
        <div className="product-grid">
          {visible.map((product) => (
            <ProductCard key={product.product_id} product={product} />
          ))}
        </div>
      )}
    </div>
  )
}
