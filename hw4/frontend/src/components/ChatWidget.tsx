import { useEffect, useMemo, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import { Link, useLocation } from 'react-router-dom'

import { fetchChatHistory, sendChatMessage } from '../api'
import { useAuth } from '../auth'
import { useChatResults } from '../chatResults'
import type { ChatMessage, PageContext } from '../types'
import ProductCard from './ProductCard'

/** Turn the current URL into the context the agent needs to resolve "this". */
function readPageContext(pathname: string): PageContext {
  const productMatch = pathname.match(/^\/products\/(.+)$/)
  if (productMatch) {
    return { page: 'product', path: pathname, product_id: decodeURIComponent(productMatch[1]) }
  }
  if (pathname === '/products') return { page: 'products', path: pathname }
  if (pathname === '/') return { page: 'home', path: pathname }
  if (pathname === '/about') return { page: 'about', path: pathname }
  if (pathname === '/login' || pathname === '/create-account') {
    return { page: 'auth', path: pathname }
  }
  return { page: 'other', path: pathname }
}

const GREETING: ChatMessage = {
  role: 'assistant',
  content:
    "Hi! I'm Bailey, the Campus Customs shop assistant. Ask me about a hoodie, a college " +
    'crewneck or what we have in your size, and I will pull the matching items onto the page.',
}

const SUGGESTIONS = [
  'What hoodies do you have?',
  'Anything for The Game?',
  'Show me a crewneck under $60',
]

/**
 * Floating chat panel, bottom right.
 *
 * Problem 3 scope: the UI is complete and it really does POST to /api/chat, but the
 * backend replies with a placeholder. Problem 5 puts the PydanticAI agent behind that
 * endpoint; the product cards below already know how to render whatever it returns.
 */
export default function ChatWidget() {
  const { user } = useAuth()
  const { setResults } = useChatResults()
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [restored, setRestored] = useState(false)
  const [returnFocus, setReturnFocus] = useState(false)

  const pageContext = useMemo(() => readPageContext(pathname), [pathname])
  const logRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const fabRef = useRef<HTMLButtonElement>(null)

  // Reload a signed-in shopper's saved conversation; reset to the greeting on log out.
  useEffect(() => {
    if (!user) {
      setMessages([GREETING])
      setRestored(false)
      return
    }
    let cancelled = false
    fetchChatHistory()
      .then((history) => {
        if (cancelled) return
        if (history.messages.length === 0) {
          setMessages([GREETING])
          setRestored(false)
          return
        }
        setMessages([
          {
            role: 'assistant',
            content: `Welcome back, ${user.first_name ?? user.name}. Here is where we left off.`,
          },
          ...history.messages.map((entry) => ({
            role: entry.role,
            content: entry.content,
            products: entry.products,
          })),
        ])
        setRestored(true)
      })
      .catch(() => undefined)
    return () => {
      cancelled = true
    }
  }, [user])

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  // Escape closes the panel and hands focus back to the launcher, so the assistant can
  // be opened, used and dismissed without a mouse.
  useEffect(() => {
    if (!open) return
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setOpen(false)
        setReturnFocus(true)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open])

  // The launcher button is only mounted once the panel is closed, so focus has to move
  // after that render rather than inside the key handler.
  useEffect(() => {
    if (open || !returnFocus) return
    fabRef.current?.focus()
    setReturnFocus(false)
  }, [open, returnFocus])

  async function send(text: string) {
    const message = text.trim()
    if (!message || sending) return

    setMessages((current) => [...current, { role: 'user', content: message }])
    setDraft('')
    setSending(true)

    try {
      const reply = await sendChatMessage(message, pageContext)
      setMessages((current) => [
        ...current,
        { role: 'assistant', content: reply.reply, products: reply.products },
      ])
      // Publish the matches so the Products page can show them too, not just the panel.
      setResults(message, reply.products)
    } catch {
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content:
            'I could not reach the shop just now. Please make sure the backend is running and try again.',
        },
      ])
    } finally {
      setSending(false)
    }
  }

  if (!open) {
    return (
      <button
        ref={fabRef}
        className="chat-fab"
        onClick={() => setOpen(true)}
        aria-label="Open shop chat with Bailey"
      >
        <span className="chat-avatar" aria-hidden="true">
          &#128054;
        </span>
        Ask Bailey
      </button>
    )
  }

  return (
    <section className="chat-panel" aria-label="Campus Customs shop chat">
      <header className="chat-head">
        <span className="chat-avatar" aria-hidden="true">
          &#128054;
          <i className="status-dot" />
        </span>
        <div>
          <strong>Bailey</strong>
          <small>{sending ? 'Checking the shelves...' : 'Online · reads live stock'}</small>
        </div>
        <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
          &times;
        </button>
      </header>

      <div className="chat-log" ref={logRef} role="log" aria-live="polite" aria-busy={sending}>
        {messages.map((message, index) => (
          <div key={index} className={`bubble ${message.role}`}>
            {message.role === 'assistant' ? (
              // Bailey writes Markdown - bold prices, bullet lists. react-markdown
              // escapes raw HTML, so a reply cannot inject markup into the page.
              <div className="md">
                <Markdown>{message.content}</Markdown>
              </div>
            ) : (
              message.content
            )}
            {message.products && message.products.length > 0 && (
              <div className="chat-cards">
                {message.products.map((product) => (
                  <ProductCard
                    key={product.product_id}
                    product={product}
                    compact
                    onNavigate={() => setOpen(false)}
                  />
                ))}
                <Link
                  className="chat-cards-link"
                  to="/products"
                  onClick={() => setOpen(false)}
                >
                  Show these on the Products page &rarr;
                </Link>
              </div>
            )}
          </div>
        ))}
        {sending && (
          <div className="typing" role="status" aria-label="Bailey is typing">
            <i />
            <i />
            <i />
          </div>
        )}
      </div>

      {messages.length <= 1 && !restored && (
        <div className="chat-suggestions">
          {SUGGESTIONS.map((suggestion) => (
            <button key={suggestion} onClick={() => void send(suggestion)}>
              {suggestion}
            </button>
          ))}
        </div>
      )}

      <form
        className="chat-input"
        onSubmit={(event) => {
          event.preventDefault()
          void send(draft)
        }}
      >
        <input
          ref={inputRef}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask about sizes, price or stock..."
          aria-label="Message"
        />
        <button
          className="chat-send"
          type="submit"
          disabled={!draft.trim() || sending}
          aria-label="Send message"
        >
          &#10148;
        </button>
      </form>
    </section>
  )
}
