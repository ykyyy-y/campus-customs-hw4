import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type { PublicUser } from './types'

const STORAGE_KEY = 'campus-customs-user'

interface AuthState {
  user: PublicUser | null
  signIn: (user: PublicUser) => void
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
 * Only the public account fields are cached in localStorage so a refresh does not throw
 * you out. The password never reaches the browser's storage because the API never
 * returns it in the first place.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<PublicUser | null>(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY)
      return saved ? (JSON.parse(saved) as PublicUser) : null
    } catch {
      return null
    }
  })

  useEffect(() => {
    if (user) window.localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
    else window.localStorage.removeItem(STORAGE_KEY)
  }, [user])

  const signIn = useCallback((next: PublicUser) => setUser(next), [])
  const signOut = useCallback(() => setUser(null), [])

  const value = useMemo(() => ({ user, signIn, signOut }), [user, signIn, signOut])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
