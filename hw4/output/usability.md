# Campus Customs — Usability Improvements

Four improvements chosen after the core shop was working: two on the front end, two in the
agent/backend. This file was written before the work and updated with verification results
after each one shipped.

Each entry says **what was added**, **why it helps the shopper or the business**, and
**where to see it in the running app**.

| # | Area | Improvement |
|---|---|---|
| 1 | Front end | Shop by your size — size + in-stock filters, with shareable URLs |
| 2 | Front end | Chat replies render as formatted text, and the panel is keyboard-usable |
| 3 | Agent | `suggest_alternatives` tool — a real second option when something is sold out |
| 4 | Backend | Catalogue cache — a faster, cheaper agent turn |

---

## 1. Front end — "Shop by your size"

### What was added

On the Products page, a row of size chips (**XS S M L XL XXL**) and an **In stock only**
toggle, alongside the existing search, garment and sort controls.

- Picking **L** narrows the catalogue to products that have L *actually on the shelf* —
  not products that merely come in L. The filter reads `sizes_in_stock`, which is computed
  from the `inventory` table, so a product whose L row is at zero disappears.
- **In stock only** hides products with no stock in any size.
- All five controls are mirrored into the URL (`?search=…&type=…&size=L&stock=in&sort=price-asc`),
  so the browser Back button steps through filter changes and a filtered view can be
  bookmarked or sent to someone.
- An active-filter summary line with a **Clear all** button, so it is always obvious why
  the grid is short.

### Why it helps

**For the shopper:** 145 of the 612 inventory rows are at zero, so browsing without a size
filter means repeatedly clicking into a product only to find your size sold out. A parent
shopping for one specific size can now see, in one step, only what they can actually buy.

**For the business:** every click into a sold-out item is a small disappointment and a
chance to leave. Filtering to real availability keeps the shopper looking at things they
can buy today, and shareable URLs let staff send "here is everything we have in XL" to a
customer over email.

### Where to see it

`/products` → the filter bar. Pick a size; the count updates and the URL changes.

---

## 2. Front end — Readable chat replies and a keyboard-friendly panel

### What was added

The agent writes Markdown — prices as `**$68.00**` and multi-product answers as bullet
lists. The chat panel was rendering that as literal text, so shoppers saw
`**$68.00**` with the asterisks, and bullet lists ran together in one block.

- Replies now render as formatted text: **bold** prices, real bullet lists, paragraph
  breaks. Rendered with `react-markdown`, which escapes raw HTML, so a reply can never
  inject markup into the page.
- The chat log is an `aria-live="polite"` region, so a screen reader announces Bailey's
  answer when it arrives instead of leaving it silent.
- **Escape** closes the panel, and focus returns to the chat button, so the panel can be
  opened, used and dismissed without a mouse.
- The send button and the panel have proper labels, and the typing indicator is announced.

### Why it helps

**For the shopper:** the price is the single most important thing in most replies, and it
was being obscured by punctuation. A list of five hoodies is now scannable rather than a
wall of text. Keyboard and screen-reader users can use the assistant at all.

**For the business:** the chatbot is the shop's voice. Asterisks around every price make a
real store look broken, and undermine trust in the numbers themselves — which is exactly
the thing the whole tool-calling design exists to protect.

### Where to see it

Open the chat and ask anything with a price. Compare the bubble to the raw reply text in
the API response.

---

## 3. Agent — `suggest_alternatives`: a real second option when something is sold out

### What was added

A new agent tool, `suggest_alternatives(product_id, size=None)`, that returns genuine
substitutes read from the database:

- Same kind of garment, matched on a normalised garment family (so `pullover hoodie`,
  `hooded sweatshirt` and `hoodie` count as one family despite 22 near-duplicate spellings
  in `catalogue.garment_type`).
- **In stock in the size the shopper asked for**, when a size was named.
- Ranked by how close the price is to the product they were already looking at, so the
  suggestion is a fair swap rather than an upsell.
- Falls back to other in-stock products of the same family when nothing matches exactly,
  and returns an empty list rather than a stretch.

The prompt now instructs the agent to call it whenever a requested size or colour is
unavailable, and to offer at most two alternatives — named, priced, and as cards.

### Why it helps

**For the shopper:** "sold out in XL" is a dead end. "Sold out in XL, but the Champion
Reverse Weave Hoodie is $68.00 and we have it in XL" is an answer. It saves them going back
to the catalogue and filtering by hand.

**For the business:** this is the difference between a lost sale and a substituted sale on
the 145 sold-out size rows. It also keeps the honesty rule intact — the agent still says no
plainly first, and the alternative is a real row from `inventory`, not a guess.

### Where to see it

Ask about a sold-out size, e.g. *"Do you have the Baseball Left Chest Crewneck in XS?"*

---

## 4. Backend — Catalogue cache: a faster, cheaper agent turn

### What was added

An in-memory, TTL'd cache of the catalogue and inventory in `db.py`.

- The catalogue is **read-only during a shopping session**: 102 products and 612 inventory
  rows that no request ever changes. Before this, every tool call re-opened SQLite, re-ran
  the join, and re-parsed the JSON `colors` and `search_tags` columns for all 102 rows —
  and a single chat turn makes several tool calls.
- Now the rows are built once and reused, with a 5-minute TTL and an explicit
  `invalidate_cache()`, so stock edits are still picked up.
- Writes (`users`, `chat_messages`) are untouched and never cached.
- `get_product()` became a dictionary lookup instead of a query.

### Why it helps

**For the shopper:** the wait after pressing Enter is the whole experience of a chatbot.
Tool calls stop being the slow part, so replies arrive sooner.

**For the business:** cheaper and more scalable. Each turn does a fraction of the disk work,
so the same machine serves far more concurrent shoppers, and `search_catalogue` — the most
called tool — no longer costs a full table read plus 102 JSON parses per call.

### Where to see it

`/api/health` reports cache state. Measured numbers are in the verification table below.

---

## Verification

All four were checked in the running app, not just in code.

### 1. Shop by your size

| Check | Result |
|---|---|
| Six size chips + In stock only toggle render on `/products` | yes |
| Unfiltered catalogue | `102 items` |
| Click **XS** | `75 items`, URL becomes `?size=XS`, chip shows `aria-pressed="true"` |
| Is 75 correct? | Yes — 75 of 102 products have XS stock above zero (checked directly against `inventory`) |
| Per-size counts in the database | XS 75 · S 78 · M 80 · L 78 · XL 77 · XXL 79 |
| Combine size + in-stock + price sort | URL `?size=XL&stock=in&sort=price-asc`, `77 items`, first four cards all `$32.00` |
| Browser **Back** | steps back through `?size=XL&stock=in` → `?size=XL`, grid follows |
| Filter summary | "Showing only what we have in **size XL** · in stock only" + Clear all |

### 2. Readable chat replies and keyboard use

Verified on the reply to *"Do you have the Baseball Left Chest Crewneck in XS?"*:

| Check | Result |
|---|---|
| Raw `**` asterisks visible in the bubble | **no** |
| `$58.00` rendered as a real `<strong>` element | yes |
| Markdown wrapper present | yes |
| Chat log exposes `role="log"` and `aria-live="polite"` | yes |
| Launcher label | "Open shop chat with Bailey" |
| **Escape** closes the panel | yes |
| Focus returns to the launcher after Escape | yes |

One bug was found and fixed during this check: the first version called
`fabRef.current?.focus()` inside the key handler, but the launcher button is only mounted
*after* the panel closes, so the ref was null and focus went nowhere. Focus now moves in an
effect that runs after that render.

### 3. `suggest_alternatives`

Tool level, against the live database:

| Case | Result |
|---|---|
| Baseball Left Chest Crewneck, XS (sold out) | 3 crewnecks at `$58.00`, **all with XS actually in stock**; basis: "same kind of garment (crewneck), in stock in XS" |
| Crew Left Chest Hoodie, M (sold out) | 3 hoodies at `$68.00`, all with M in stock |
| Unknown product id | `None`, not a guess |
| Garment family grouping | `pullover hoodie` → hoodie · `full-zip hooded sweatshirt` → hoodie · `raglan crewneck sweatshirt` → crewneck · `quarter-zip pullover` → quarter-zip · `bomber jacket` → jacket · `heavyweight short-sleeve t-shirt` → t-shirt |

Live, through the website chat:

> **"Do you have the Baseball Left Chest Crewneck in XS?"**
>
> "The Baseball Left Chest Crewneck is sold out in XS. We do have it in S, M, L, and XXL.
> If another crewneck would work, the Davenport College Crewneck and District Vintage
> Bulldog Crewneck are both **$58.00** and available in XS."

Three clickable cards rendered with it. Note the order: the **no comes first**, the
alternative second — which is what the prompt requires.

### 4. Catalogue cache

Measured over 200 calls each, same machine, cache off vs on:

| Operation | Uncached | Cached | Effect |
|---|---|---|---|
| `get_product()` | 5.407 ms | <0.001 ms | now a dictionary lookup rather than two queries |
| `search_catalogue("hoodies")` | 10.702 ms | 4.273 ms | **2.5× faster** |
| `catalogue_stats()` | 5.772 ms | 0.018 ms | **324× faster** |

`search_catalogue` keeps a real cost because the token scoring still runs over all 102
products; what the cache removes is the table read and the 102 JSON parses underneath it.

Live cache state from `/api/health` after the browser testing above:

```json
"catalogue_cache": { "cached_products": 102, "hits": 12, "misses": 1, "ttl_seconds": 300 }
```

A **92% hit rate** across ordinary use — one load, then everything served from memory.
Correctness was re-checked after the rewrite: 102 products, 22 garment types, `$32.00`–
`$98.00`, 5,920 units, 27 hoodie matches, and `None` still returned for an unknown id.

---

## Notes and honest limits

- The cached product dictionaries are shared, not copied, so callers must treat them as
  read-only. Every current caller does — the tools read fields and `Product(**row)` builds
  a fresh model — but it is a constraint a future change has to respect.
- `PageContext` can also carry the catalogue `search` and `garment_type`; now that filters
  live in the URL, wiring those through to the agent is a natural next step.
- The cache TTL is 5 minutes (`CAMPUS_CUSTOMS_CACHE_TTL`). For a real shop with live
  inventory writes, `invalidate_cache()` should be called on stock updates instead of
  relying on the TTL.
