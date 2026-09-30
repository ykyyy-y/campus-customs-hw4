import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { fetchMe, logout as logoutRequest, setSessionToken } from './api'
import type { PublicUser } from './types'

const USER_KEY = 'campus-customs-user'
const TOKEN_KEY = 'campus-customs-session'

interface AuthState {
  user: PublicUser | null
  signIn: (user: PublicUser, token: string) => void
  signOut: () => void
}

const AuthContext = createContext<AuthState>({
  user: null,
  signIn: () => undefined,
  signOut: () => undefined,
})

/**
 * Keeps the signed-in shopper available to every page.
 *
 * Two things are cached so a refresh does not throw you out: the public account fields
 * (for instant rendering) and the **session token** (which is what actually proves who
 * later requests are from). The cached account is treated as a convenience only - it is
 * re-validated against `/api/me` on load, and dropped if the token is no longer a live
 * session, so editing the cached copy in devtools gains nothing.
 *
 * The password is never here, because the API never returns it.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<PublicUser | null>(() => {
    try {
      const token = window.localStorage.getItem(TOKEN_KEY)
      const saved = window.localStorage.getItem(USER_KEY)
      // Without a token there is no session, so a cached account is meaningless.
      if (!token || !saved) return null
      setSessionToken(token)
      return JSON.parse(saved) as PublicUser
    } catch {
      return null
    }
  })

  // Confirm the stored token is still valid, and take the account from the server's
  // answer rather than from whatever the browser had cached.
  useEffect(() => {
    if (!window.localStorage.getItem(TOKEN_KEY)) return
    let cancelled = false
    fetchMe()
      .then((fresh) => {
        if (!cancelled) {
          setUser(fresh)
          window.localStorage.setItem(USER_KEY, JSON.stringify(fresh))
        }
      })
      .catch(() => {
        if (cancelled) return
        // Expired or revoked session: clear it rather than showing a stale identity.
        setSessionToken(null)
        window.localStorage.removeItem(TOKEN_KEY)
        window.localStorage.removeItem(USER_KEY)
        setUser(null)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const signIn = useCallback((next: PublicUser, token: string) => {
    setSessionToken(token)
    window.localStorage.setItem(TOKEN_KEY, token)
    window.localStorage.setItem(USER_KEY, JSON.stringify(next))
    setUser(next)
  }, [])

  const signOut = useCallback(() => {
    // Tell the server to forget the session, so the token cannot be replayed.
    void logoutRequest().catch(() => undefined)
    setSessionToken(null)
    window.localStorage.removeItem(TOKEN_KEY)
    window.localStorage.removeItem(USER_KEY)
    setUser(null)
  }, [])

  const value = useMemo(() => ({ user, signIn, signOut }), [user, signIn, signOut])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
