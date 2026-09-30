import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { fetchProducts, fetchStats } from '../api'
import HeroShowcase from '../components/HeroShowcase'
import ProductCard from '../components/ProductCard'
import type { CatalogueStats, Product } from '../types'

// Real products for the hero showcase, chosen to span the range: a hoodie, the rivalry
// tee, a classic crewneck, a quarter-zip and a jacket.
const HERO_PICKS = [
  'basic-hoodie-big-yale',
  '2025-yale-vs-harvard-t-shirt',
  'champion-reverse-weave-crewneck',
  'branford-1-4-zip',
  'brooks-brothers-bomber-jacket-yale',
]

const PROMISES = [
  {
    icon: '\u{1F9F5}',
    title: 'Printed where you walk to class',
    body: 'Screen printing and embroidery happen in our own shop, a few blocks from Old Campus, not in a warehouse three states away.',
  },
  {
    icon: '\u{1F3DB}',
    title: 'Fifty years on Broadway',
    body: 'We opened in 1975 and have been outfitting students, parents and returning alumni from the same corner ever since.',
  },
  {
    icon: '\u{2714}',
    title: 'Officially licensed, every stitch',
    body: 'Every wordmark and bulldog on this page is licensed by the University, so the gear you buy is the real thing.',
  },
]

export default function Home() {
  const [featured, setFeatured] = useState<Product[]>([])
  const [heroImages, setHeroImages] = useState<Product[]>([])
  const [stats, setStats] = useState<CatalogueStats | null>(null)

  useEffect(() => {
    fetchProducts()
      .then((products) => {
        const picks = HERO_PICKS.map((id) =>
          products.find((product) => product.product_id === id),
        ).filter((product): product is Product => Boolean(product))
        setHeroImages(picks.length >= 3 ? picks : products.slice(0, 5))
        setFeatured(products.filter((product) => product.total_stock > 0).slice(0, 4))
      })
      .catch(() => undefined)
    fetchStats()
      .then(setStats)
      .catch(() => undefined)
  }, [])

  return (
    <div className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">57 Broadway &middot; New Haven, CT</p>
          <h1>
            Yale gear that is made <em>down the street</em>, not shipped in.
          </h1>
          <p className="lede">
            Campus Customs has been the neighbourhood answer to "where did you get that
            sweatshirt?" since 1975. Pull on a heavyweight crewneck for a cold walk to
            Sterling, grab a residential college tee before move-in, or pick up something in
            blue for the family coming up for The Game.
          </p>
          <div className="hero-actions">
            <Link className="btn btn-primary" to="/products">
              Shop the catalogue
            </Link>
            <Link className="btn btn-ghost" to="/about">
              Our story
            </Link>
          </div>
          <div className="hero-stats">
            <div>
              <strong>{stats ? stats.products : '—'}</strong>
              <span>Styles online</span>
            </div>
            <div>
              <strong>1975</strong>
              <span>On Broadway since</span>
            </div>
            <div>
              <strong>
                {stats ? `$${Math.round(stats.min_price)}–$${Math.round(stats.max_price)}` : '—'}
              </strong>
              <span>Price range</span>
            </div>
          </div>
        </div>

        <HeroShowcase products={heroImages} />
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <p className="eyebrow">Why shop with us</p>
            <h2>A campus shop, not a catalogue company</h2>
          </div>
        </div>
        <div className="card-row">
          {PROMISES.map((promise) => (
            <article className="info-card" key={promise.title}>
              <div className="icon" aria-hidden="true">
                {promise.icon}
              </div>
              <h3>{promise.title}</h3>
              <p>{promise.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <p className="eyebrow">Fresh on the rack</p>
            <h2>Picked out for this week</h2>
          </div>
          <Link className="btn btn-ghost" to="/products">
            See all styles
          </Link>
        </div>
        {featured.length > 0 ? (
          <div className="product-grid">
            {featured.map((product) => (
              <ProductCard key={product.product_id} product={product} />
            ))}
          </div>
        ) : (
          <div className="skeleton-grid">
            {[0, 1, 2, 3].map((index) => (
              <div className="skeleton" key={index} />
            ))}
          </div>
        )}
      </section>

      <section className="section">
        <article className="info-card" style={{ padding: '2.25rem' }}>
          <p className="eyebrow">Not sure what you want?</p>
          <h2 style={{ fontSize: '1.6rem' }}>Ask Bailey, our shop assistant</h2>
          <p className="lede" style={{ marginBottom: 0 }}>
            Tap the chat bubble in the corner and describe what you are after &mdash; a warm
            quarter-zip, something in your residential college, a gift under sixty dollars.
            Bailey reads the same stock list our register does, so the price and the size
            you hear are the ones on the shelf.
          </p>
        </article>
      </section>
    </div>
  )
}
