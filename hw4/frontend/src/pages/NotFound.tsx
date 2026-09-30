import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="page state">
      <p className="eyebrow">404</p>
      <h2>That rack is empty</h2>
      <p>The page you were after is not here. The catalogue is, though.</p>
      <Link className="btn btn-primary" to="/products">
        Browse the catalogue
      </Link>
    </div>
  )
}
