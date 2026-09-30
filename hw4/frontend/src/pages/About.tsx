import { Link } from 'react-router-dom'

const MILESTONES = [
  {
    year: '1975',
    title: 'A small shop opens on Broadway',
    body: 'Campus Customs starts printing shirts a short walk from Old Campus, and quickly becomes the place students go when a team, a club or a suite needs something made.',
  },
  {
    year: 'Forty years behind the counter',
    title: 'A family business, still family run',
    body: 'The Cobden family has run the shop across two generations. The person sizing your sweatshirt has usually been doing it for longer than you have been at Yale.',
  },
  {
    year: '2005',
    title: 'The old cinema becomes our workroom',
    body: 'When the York Square Cinema closed, we took the building on as our production space. The embroidery machines and silk-screen presses live there today.',
  },
  {
    year: 'Now',
    title: 'The oldest licensed Yale retailer in town',
    body: 'We carry one of the widest selections of Yale merchandise anywhere, from residential college crewnecks to varsity team tees to something small for a niece back home.',
  },
]

export default function About() {
  return (
    <div className="page">
      <p className="eyebrow">About us</p>
      <h1 style={{ fontSize: 'clamp(2.1rem, 4vw, 3rem)', maxWidth: '18ch' }}>
        Fifty years of putting Yale on cotton.
      </h1>
      <p className="lede" style={{ marginTop: '1rem' }}>
        Campus Customs is a shop at 57 Broadway in New Haven, not a brand invented for a
        website. We have been here since 1975, we are the oldest officially licensed Yale
        merchandise retailer in the city, and almost everything we sell is printed or
        embroidered by our own people a few hundred yards from where you are standing.
      </p>

      <section className="section">
        <div className="section-head">
          <div>
            <p className="eyebrow">How we got here</p>
            <h2>The short version</h2>
          </div>
        </div>
        <div className="card-row">
          {MILESTONES.map((milestone) => (
            <article className="info-card" key={milestone.title}>
              <p className="eyebrow" style={{ marginBottom: '0.35rem' }}>
                {milestone.year}
              </p>
              <h3>{milestone.title}</h3>
              <p>{milestone.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <p className="eyebrow">What we actually do</p>
            <h2>Made here, not ordered in</h2>
          </div>
        </div>
        <div className="card-row">
          <article className="info-card">
            <div className="icon" aria-hidden="true">
              {'\u{1F5A8}'}
            </div>
            <h3>Screen printing</h3>
            <p>
              Team shirts, rush orders for a club, one hundred tanks for an intramural
              season. We run the presses ourselves, so we can tell you honestly whether a
              deadline is realistic.
            </p>
          </article>
          <article className="info-card">
            <div className="icon" aria-hidden="true">
              {'\u{1F9F5}'}
            </div>
            <h3>Embroidery</h3>
            <p>
              Left-chest wordmarks, residential college shields, a name stitched onto a
              quarter-zip for graduation. Custom work goes on the same machines that stitch
              our shelf stock.
            </p>
          </article>
          <article className="info-card">
            <div className="icon" aria-hidden="true">
              {'\u{1F393}'}
            </div>
            <h3>Gear for the whole family</h3>
            <p>
              Parents' weekend, reunions, a first-year moving in, a grandchild who wants a
              bulldog on something. We stock sizes from XS to XXL and keep the classics in
              stock year round.
            </p>
          </article>
        </div>
      </section>

      <section className="section">
        <article className="info-card" style={{ padding: '2.25rem' }}>
          <h2 style={{ fontSize: '1.5rem' }}>Come by, or ask first</h2>
          <p className="lede">
            You will find us at 57 Broadway. If you would rather check before you walk over,
            open the chat in the corner &mdash; Bailey can tell you what is on the shelf in
            your size and what it costs, straight from our stock list.
          </p>
          <div className="hero-actions">
            <Link className="btn btn-primary" to="/products">
              Browse the catalogue
            </Link>
            <Link className="btn btn-ghost" to="/create-account">
              Create an account
            </Link>
          </div>
        </article>
      </section>
    </div>
  )
}
