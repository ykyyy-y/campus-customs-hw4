/** Thin client for the Campus Customs API.
 *
 * Vite proxies /api and /media to the FastAPI server on port 8000 (see vite.config.ts),
 * so these are same-origin requests from the browser's point of view.
 */

import type {
  AuthResponse,
  CatalogueStats,
  ChatHistoryResponse,
  ChatReply,
  PageContext,
  Product,
} from './types'

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(
      response.status === 404
        ? 'We could not find that item.'
        : `The shop could not be reached (${response.status}). Is the backend running on port 8000?`,
    )
  }
  return (await response.json()) as T
}

export function fetchProducts(params: { search?: string; garmentType?: string } = {}) {
  const query = new URLSearchParams()
  if (params.search?.trim()) query.set('search', params.search.trim())
  if (params.garmentType) query.set('garment_type', params.garmentType)
  const suffix = query.toString() ? `?${query}` : ''
  return getJson<Product[]>(`/api/products${suffix}`)
}

export function fetchProduct(productId: string) {
  return getJson<Product>(`/api/products/${encodeURIComponent(productId)}`)
}

export function fetchGarmentTypes() {
  return getJson<string[]>('/api/garment-types')
}

export function fetchStats() {
  return getJson<CatalogueStats>('/api/stats')
}

/** POST helper that surfaces the backend's own `detail` message to the shopper. */
async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    const detail = (payload as { detail?: unknown } | null)?.detail
    if (typeof detail === 'string') throw new Error(detail)
    // FastAPI validation errors arrive as a list of objects.
    if (Array.isArray(detail) && detail[0]?.msg) throw new Error(String(detail[0].msg))
    throw new Error('Something went wrong. Please try again.')
  }
  return payload as T
}

export function signup(input: {
  first_name: string
  last_name: string
  email: string
  password: string
}) {
  return postJson<AuthResponse>('/api/signup', input)
}

export function login(input: { email: string; password: string }) {
  return postJson<AuthResponse>('/api/login', input)
}

/** Send one shopper turn, with who they are and where they are on the site. */
export async function sendChatMessage(
  message: string,
  userId?: number,
  pageContext?: PageContext,
): Promise<ChatReply> {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      user_id: userId ?? null,
      page_context: pageContext ?? null,
    }),
  })
  if (!response.ok) {
    throw new Error('The chat service is not reachable right now.')
  }
  return (await response.json()) as ChatReply
}

/** Reload a signed-in shopper's saved conversation. Guests have none. */
export function fetchChatHistory(userId: number) {
  return getJson<ChatHistoryResponse>(`/api/chat/history?user_id=${userId}`)
}
