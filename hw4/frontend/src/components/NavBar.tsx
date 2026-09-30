import { NavLink, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth'

const LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products', end: false },
  { to: '/about', label: 'About Us', end: false },
]

export default function NavBar() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  return (
    <nav className="nav">
      <div className="nav-inner">
        <NavLink to="/" className="brand">
          <span className="brand-mark">CC</span>
          <span className="brand-text">
            <strong>Campus Customs</strong>
            <span>Broadway &middot; New Haven</span>
          </span>
        </NavLink>

        <div className="nav-links">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              {link.label}
            </NavLink>
          ))}

          {user ? (
            <>
              <span className="nav-greeting">Hi, {user.first_name ?? user.name}</span>
              <button
                className="nav-link"
                style={{ border: 'none', background: 'none', cursor: 'pointer' }}
                onClick={() => {
                  signOut()
                  navigate('/')
                }}
              >
                Log Out
              </button>
            </>
          ) : (
            <>
              <NavLink
                to="/login"
                className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
              >
                Log In
              </NavLink>
              <NavLink
                to="/create-account"
                className={({ isActive }) =>
                  isActive ? 'nav-link nav-cta active' : 'nav-link nav-cta'
                }
              >
                Create Account
              </NavLink>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
