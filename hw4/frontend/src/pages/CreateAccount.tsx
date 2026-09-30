import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { signup } from '../api'
import { useAuth } from '../auth'

/** Create an account. The row lands in `users` with a salted PBKDF2 password hash. */
export default function CreateAccount() {
  const { signIn } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirm: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  function update(field: keyof typeof form) {
    return (event: React.ChangeEvent<HTMLInputElement>) =>
      setForm((current) => ({ ...current, [field]: event.target.value }))
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setError(null)

    // Checked here for a fast, friendly message; the backend enforces both rules again.
    if (form.password.length < 8) {
      setError('Please choose a password of at least 8 characters.')
      return
    }
    if (form.password !== form.confirm) {
      setError('Those two passwords do not match.')
      return
    }

    setBusy(true)
    try {
      const result = await signup({
        first_name: form.firstName,
        last_name: form.lastName,
        email: form.email,
        password: form.password,
      })
      signIn(result.user, result.session_token)
      navigate('/products')
    } catch (cause) {
      setError((cause as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page">
      <div className="auth-wrap">
        <div className="auth-card">
          <p className="eyebrow">Join the shop</p>
          <h1>Create your account</h1>
          <p style={{ color: 'var(--text-soft)', fontSize: '0.93rem', margin: 0 }}>
            An account saves your chat history with Bailey so the shop remembers what you
            were looking for. We only ask for what we need.
          </p>

          <form className="form-grid" onSubmit={submit}>
            <div className="form-row">
              <div className="form-field">
                <label htmlFor="firstName">First name</label>
                <input
                  id="firstName"
                  required
                  value={form.firstName}
                  onChange={update('firstName')}
                  placeholder="Ada"
                  autoComplete="given-name"
                />
              </div>
              <div className="form-field">
                <label htmlFor="lastName">Last name</label>
                <input
                  id="lastName"
                  required
                  value={form.lastName}
                  onChange={update('lastName')}
                  placeholder="Lovelace"
                  autoComplete="family-name"
                />
              </div>
            </div>

            <div className="form-field">
              <label htmlFor="signupEmail">Email</label>
              <input
                id="signupEmail"
                type="email"
                required
                value={form.email}
                onChange={update('email')}
                placeholder="you@yale.edu"
                autoComplete="email"
              />
            </div>

            <div className="form-field">
              <label htmlFor="signupPassword">Password</label>
              <input
                id="signupPassword"
                type="password"
                required
                value={form.password}
                onChange={update('password')}
                placeholder="At least 8 characters"
                autoComplete="new-password"
              />
            </div>

            <div className="form-field">
              <label htmlFor="confirm">Confirm password</label>
              <input
                id="confirm"
                type="password"
                required
                value={form.confirm}
                onChange={update('confirm')}
                placeholder="Type it once more"
                autoComplete="new-password"
              />
            </div>

            {error && (
              <div className="notice" role="alert">
                {error}
              </div>
            )}

            <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
              {busy ? 'Creating your account...' : 'Create account'}
            </button>
          </form>

          <p className="form-note">
            Already shop with us? <Link to="/login">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
