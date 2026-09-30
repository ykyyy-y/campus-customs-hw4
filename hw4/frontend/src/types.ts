/** Shapes returned by the FastAPI backend. Mirrors backend/models.py. */

export interface InventoryItem {
  size: string
  quantity: number
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_file_path: string
  image_url: string
  price: number
  inventory: InventoryItem[]
  total_stock: number
  sizes_in_stock: string[]
}

export interface CatalogueStats {
  products: number
  min_price: number
  max_price: number
  units_in_stock: number
}

export interface ChatReply {
  reply: string
  products: Product[]
  saved: boolean
}

/** Where the shopper is when they send a message, so "this" resolves to a product. */
export interface PageContext {
  page: 'home' | 'products' | 'product' | 'about' | 'auth' | 'other'
  path: string
  product_id?: string | null
  search?: string | null
  garment_type?: string | null
}

export interface ChatHistoryMessage {
  id: number
  role: ChatRole
  content: string
  products: Product[]
  created_at: string | null
}

export interface ChatHistoryResponse {
  user_id: number
  messages: ChatHistoryMessage[]
}

/** An account as the API describes it. There is deliberately no password field. */
export interface PublicUser {
  id: number
  name: string
  email: string
  first_name: string | null
  last_name: string | null
  created_at: string | null
}

export interface AuthResponse {
  user: PublicUser
  message: string
  /** Proves who later requests come from; sent back as `Authorization: Bearer <token>`. */
  session_token: string
}

export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  role: ChatRole
  content: string
  products?: Product[]
}
