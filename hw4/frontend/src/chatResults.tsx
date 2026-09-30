import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type { Product } from './types'

/**
 * The products Bailey matched on the shopper's last question.
 *
 * This lives above the router so two different places can render the same result set:
 * the chat panel (cards inside the reply) and the Products page (a highlighted strip
 * above the full catalogue). That is what makes chat results "appear on the page" rather
 * than only inside the conversation.
 */
interface ChatResultsState {
  products: Product[]
  query: string | null
  setResults: (query: string, products: Product[]) => void
  clear: () => void
}

const ChatResultsContext = createContext<ChatResultsState>({
  products: [],
  query: null,
  setResults: () => undefined,
  clear: () => undefined,
})

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [products, setProducts] = useState<Product[]>([])
  const [query, setQuery] = useState<string | null>(null)

  const setResults = useCallback((nextQuery: string, nextProducts: Product[]) => {
    // A reply with no products is not a new result set - keep the last useful one on the
    // page rather than blanking it because the shopper said "thanks".
    if (nextProducts.length === 0) return
    setQuery(nextQuery)
    setProducts(nextProducts)
  }, [])

  const clear = useCallback(() => {
    setProducts([])
    setQuery(null)
  }, [])

  const value = useMemo(
    () => ({ products, query, setResults, clear }),
    [products, query, setResults, clear],
  )

  return <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
}

export function useChatResults() {
  return useContext(ChatResultsContext)
}
