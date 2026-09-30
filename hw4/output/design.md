# Campus Customs — Design System

A blush-pink, rose-slate storefront built to read like a boutique rather than a campus
bookstore website. Every change below is on the running site, and every colour, font and
motion value comes from one token block at the top of `frontend/src/index.css`.

**The commercial argument in one line:** shoppers decide whether a store is trustworthy in
well under a second, and the two things they judge are type and finish. A $68 hoodie sells
better from a page that looks like it costs $68.

---

## 1. Colour — blush stage, rose-slate ink, violet accent

| Role | Token | Value |
|---|---|---|
| Base background | `--blush` | `#fde8ed` |
| Body text | `--slate-800` | `#1e293b` |
| Headlines | `--slate-900` | `#0f172a` |
| Accent | `--violet` / `--violet-deep` | `#8b5cf6` / `#6d38e0` |
| Warmth | `--rose` / `--rose-deep` | `#d6537c` / `#b23a62` |

The body is not a flat fill. Three large radial gradients — white at top-left, violet-soft
at top-right, deeper blush at the bottom — sit on a fixed background layer, so scrolling
moves content across a lit stage. A flat pink reads as an unfinished template; a graded one
reads as art direction.

**Violet is used sparingly and on purpose:** eyebrow kickers, the growing nav underline,
focus rings, the active size chip, prices inside chat replies, and the assistant's glow.
It marks *interaction*, so the eye learns in one page that violet means clickable.

**Why it helps:** the palette is soft but the type is nearly black, so nothing has to be
squinted at. Measured contrast:

| Pair | Ratio | WCAG |
|---|---|---|
| `#1e293b` body on `#fde8ed` | **12.50:1** | AAA |
| `#0f172a` headline on `#fde8ed` | **15.25:1** | AAA |
| `#475569` secondary on `#fde8ed` | **6.47:1** | AA (AAA at large sizes) |
| `#6d38e0` accent on white | **6.38:1** | AA |

A pretty page that is hard to read loses sales. This one is chic *and* legible — a parent
reading product copy on a phone in daylight can do it.

---

## 2. Typography — Syne display over Plus Jakarta Sans

- **Syne** (600–800) for every `h1/h2/h3`, prices and stat numbers, at `-0.03em` to
  `-0.045em` tracking. Syne has the slightly odd, high-fashion proportions of a lookbook
  masthead — it does not look like a default web font, which is the point.
- **Plus Jakarta Sans** (400–800) for body, labels and UI. Tall x-height, open apertures,
  crisp at 14–16px.

The hero runs `clamp(2.7rem, 6.2vw, 4.6rem)` so the headline is genuinely large on desktop
and never breaks on a phone. The word "down the street" is filled with a rose→violet
gradient via `background-clip: text` — one editorial moment, not a page of them.

**Why it helps:** the display/body pairing creates instant hierarchy. A shopper scanning
the catalogue reads *product name → price → stock* in that order without being told to,
because the price is set in the display face and the name is not. Prices being the most
typographically confident thing on a card removes the "how much is this?" friction that
makes people leave.

---

## 3. Product presentation — 3D tilt, floating live badges, quick view

Each card is wrapped in a `Tilt` component (`components/Tilt.tsx`):

- The wrapper owns `perspective: 1000px`; only the card rotates, up to **±7°**, following
  the pointer. Text stays crisp because a single element is transformed.
- A **specular highlight** tracks the cursor across the photo via `--mx`/`--my` custom
  properties and a radial gradient — the sheen of light moving over fabric.
- The photo scales to 1.07 and the shadow deepens to `--shadow-3`, so the card physically
  approaches the shopper.
- Transform writes are batched inside `requestAnimationFrame`, so a fast mouse cannot queue
  more style changes than the browser can paint.

**Floating stock badges** sit at `translateZ(40px)` — above the card in 3D space, on frosted
glass — with a **live availability dot**:

| State | Dot | Pulse |
|---|---|---|
| In stock | green `#18b26b` | slow, 2.2s |
| Only N left | amber `#f59e0b` | urgent, 1.1s |
| Sold out | grey, static | none |

**Quick view →** fades up in the card footer on hover.

**Why it helps:** tilt and parallax make browsing feel tactile, which measurably increases
time on a grid — but the badge is the commercial part. 145 of 612 size rows are at zero, so
availability is the single most decision-relevant fact about any product. Putting it on the
photo, with a dot that beats *faster* when stock is low, converts honest data into gentle
urgency: "only 3 left" is a reason to buy now, and it is true, because it is read from
`inventory`.

---

## 4. Chat — glassmorphism, live status, ambient glow

- The panel is **frosted glass**: `rgba(255,255,255,0.72)` over
  `backdrop-filter: blur(28px) saturate(170%)`, a bright `inset` top edge, 28px radius and
  a deep layered shadow. The store blurs *through* it, so the assistant floats above the
  page instead of covering it.
- The launcher carries an **ambient micro-glow** — a blurred violet→rose aura behind the
  pill, breathing on a 3.4s loop — so the assistant reads as alive without a badge shouting
  for attention.
- A **pulsing green status dot** on Bailey's avatar, with a subtitle that switches from
  "Online · reads live stock" to "Checking the shelves…" while a reply is in flight.
- **Animated typing indicator**: three violet dots bouncing on staggered 0.16s delays.
- Bubbles enter with a 0.35s rise; the panel itself scales in from 0.97.

**Why it helps:** shoppers distrust chatbots by default. "Online · reads live stock" plus a
live pulse tells them two things before they type — someone is there, and the answers come
from real stock. The typing indicator is what stops people giving up during the two or three
seconds a tool-calling turn takes; without it, silence reads as broken. Glass keeps the
product they were looking at visible behind the conversation, so asking a question never
means losing their place.

---

## 5. Dynamic hero showcase

`components/HeroShowcase.tsx` replaces the static image collage with a live merchandise
carousel of five real catalogue products — a hoodie, the Harvard–Yale tee, a classic
crewneck, a quarter-zip and a bomber jacket.

- Auto-rotates every 5.2s with a cross-fade and a slight scale, the image swapping under a
  dark gradient scrim.
- Each frame overlays garment type, **name**, **real price**, a **live stock badge**, and a
  glass **View item →** button linking straight to that product.
- A thumbnail rail below lets the shopper **take over**; rotation stops on the first click
  or hover and does not restart, so it never fights the person using it.
- Honours `prefers-reduced-motion`: no auto-rotation at all, thumbnails still work.

**Why it helps:** a static hero shows one thing; this one advertises five, with price and
availability, in the same space. It turns the top of the home page from decoration into a
shoppable surface — and because the thumbnails hand control over immediately, a shopper who
sees something they like can stop the carousel and click it instead of waiting for it to
come back around. Every frame is a real product with a real link, so the most attractive
pixels on the site are also the shortest path to a product page.

---

## 6. Motion discipline and accessibility

Design that only works for some people is unfinished.

- One shared easing curve, `cubic-bezier(0.22, 1, 0.36, 1)`, on every transition — the site
  moves with one personality rather than five.
- **`prefers-reduced-motion: reduce`** collapses all animation and transition durations to
  ~0ms, cancels hover lifts, and stops the hero rotating. `Tilt` and `HeroShowcase` check
  the same query in JavaScript, so the tilt maths never runs either.
- Visible `:focus-visible` ring in violet at 2px with 3px offset on every interactive
  element.
- Size chips expose `aria-pressed`; showcase thumbnails expose `aria-current` and a label
  naming the product; the chat log is an `aria-live="polite"` region; Escape closes the
  panel and returns focus to the launcher.

---

## Verified in the running app

| Check | Result |
|---|---|
| `body` background | `rgb(253, 232, 237)` = `#fde8ed` ✓ |
| `body` colour | `rgb(30, 41, 59)` = `#1e293b` ✓ |
| `--violet` token | `#8b5cf6` ✓ |
| Body font resolved | `"Plus Jakarta Sans", …` ✓ |
| `h1` font resolved | `Syne, …` ✓ |
| Hero showcase | stage + **5 thumbnails**, auto-rotated to a new product unprompted |
| Thumbnail takeover | clicked thumb 0 → headline changed *Branford 1 4 Zip* → *Basic Hoodie Big Yale*, price → `$68.00`, CTA → `/products/basic-hoodie-big-yale` |
| 3D tilt maths | top-right pointer → `rotateX(5.6deg) rotateY(5.6deg)`; bottom-left → `rotateX(-5.6deg) rotateY(-5.6deg)`; highlight `--mx/--my` tracked to `90%/10%` and `10%/90%`; reset to none on pointer-out |
| Floating badges / live dots | 5 badges and 5 pulsing dots on the home page; `pulse-ring` animation active |
| Chat panel glass | `backdrop-filter: blur(28px) saturate(1.7)`, `rgba(255,255,255,0.72)`, 28px radius, `chat-in` entry animation |
| Launcher ambient glow | `::before` running the `ambient` keyframes with `blur(12px)` |
| Live status | green `rgb(24,178,107)` dot running `pulse-ring`, subtitle "Online · reads live stock" |
| Contrast | 12.50:1 body, 15.25:1 headings — both AAA |
| Console errors / failed requests | none / none |
| `tsc -b` | clean |

One note on how the tilt was verified: the Browser pane reports `document.hidden = true`, so
Chrome pauses `requestAnimationFrame` there and the tilt cannot paint. The numbers above
were produced by running the rAF callback synchronously to exercise the identical code path
a visible tab takes.
