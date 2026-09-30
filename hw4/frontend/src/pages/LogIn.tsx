import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { login } from '../api'
import { useAuth } from '../auth'

/** Sign in with email and password, checked against the hashed password in `users`. */
export default function LogIn() {
  const { user, signIn, signOut } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const result = await login({ email, password })
      signIn(result.user)
      navigate('/products')
    } catch (cause) {
      setError((cause as Error).message)
    } finally {
      setBusy(false)
    }
  }

  if (user) {
    return (
      <div className="page">
        <div className="auth-wrap">
          <div className="auth-card">
            <p className="eyebrow">Signed in</p>
            <h1>Hi, {user.first_name ?? user.name}</h1>
            <p style={{ color: 'var(--text-soft)', fontSize: '0.93rem' }}>
              You are logged in as {user.email}.
            </p>
            <div className="form-grid">
              <Link className="btn btn-primary btn-block" to="/products">
                Keep shopping
              </Link>
              <button className="btn btn-ghost btn-block" onClick={signOut}>
                Log out
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="auth-wrap">
        <div className="auth-card">
          <p className="eyebrow">Welcome back</p>
          <h1>Log in to Campus Customs</h1>
          <p style={{ color: 'var(--text-soft)', fontSize: '0.93rem', margin: 0 }}>
            Signing in keeps your chat with Bailey on file, so you can pick up a
            conversation about sizes exactly where you left it.
          </p>

          <form className="form-grid" onSubmit={submit}>
            <div className="form-field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@yale.edu"
                autoComplete="email"
              />
            </div>
            <div className="form-field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Your password"
                autoComplete="current-password"
              />
            </div>

            {error && (
              <div className="notice" role="alert">
                {error}
              </div>
            )}

            <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
              {busy ? 'Checking...' : 'Log in'}
            </button>
          </form>

          <p className="form-note">
            New here? <Link to="/create-account">Create an account</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
