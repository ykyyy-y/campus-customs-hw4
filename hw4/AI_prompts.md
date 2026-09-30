# HW 4 — Campus Customs: Vibe Coder Prompt Log

**Course:** 409 AI for Managers — AI Foundation
**Assignment:** HW 4 — Campus Customs storefront (React + Vite + TypeScript front end, Python FastAPI backend, PydanticAI agent brain, local SQLite for price/stock truth)
**Author:** Yookyung Eom
**Started:** 2026-09-28

## How this log works

This file is the running record of every prompt I typed to the vibe coder while building
this assignment. It is updated as each of the 13 problems is completed, not reconstructed
afterward.

Each problem below has exactly three parts, per the assignment spec:

1. **Problem number and title**
2. **At least one prompt I typed** — recorded verbatim, as typed
3. **One follow-up prompt if I needed it** — plus one sentence on what was lacking after
   the first prompt. Where the first prompt was sufficient, that is stated explicitly.

Evidence of the work itself is the running site, the database writes, and the
screenshots — no separate proof write-up is included here beyond these prompts.

---

## Problem 1 — Vibe Coder Prompts

Create the prompt log itself: one section per problem, each with the problem number and
title, at least one prompt typed, and a follow-up prompt if one was needed.

### Prompt I typed

> now starting with problem1: Vibe coder Prompts
>
> please create an AI_prompts.md file right now at the start of this assignment and keep
> updating it as we work, since this file will serve as a log of everything i type to you.
> make sure to create one section for each problem, and each section needs to include the
> three parts
> - the problem number and title,
> - at least one prompt i typed
> - one follow up prompt if you needed it (and one sentence explaining what was lacking
>   after the first)
>
> the running site, database writes, and screenshots will serve as the evidence, so no
> extra proof essay is needed beyond these prompts.

### Follow-up prompt

No follow-up prompt was needed; the first prompt was sufficient. The first prompt specified
the file name, its location, its purpose as a living log, the per-problem sectioning, and
all three required parts within each section, so `AI_prompts.md` was created correctly on
the first attempt.

---

## Problem 2 — Analyze the Database

Understand every table and field in `data/campus_customs.db`, then start `output/harness.md`
with each table, its fields, and one short line on why each field matters to the shop or
the chatbot.

### Prompt I typed

> Problem2: Analyze the database
>
> look at the database data/campus_customs.db and make sure you understand the fields of
> each table.
>
> at a minimum, you should understand catalogue, inventory, and users.
>
> start the file output/harness.md. write down each table and its fields, and include one
> short line on why each field matters for the shop or the chatbot. you will keep growing
> this harness file in later problems (the models, tools, safety, and specs)

### Follow-up prompt

No follow-up prompt was needed; the first prompt was sufficient. It named the database, the
minimum tables to cover, the output file, the per-field "why it matters" requirement, and
the fact that the harness would keep growing, so the coder documented all four tables
(`catalogue`, `inventory`, `users`, `chat_messages`), ran integrity checks against the live
database, and left numbered stubs for the models, tools, safety, and specs sections.

---

## Problem 3 — Build the Campus Customs Website

Scaffold the React + Vite + TypeScript front end with a nav bar, Home and About Us pages
written in our own voice, a Products page driven by the catalogue, a single-item page, a
floating chat stub, and a starter FastAPI backend in `backend/main.py`.

### Prompt I typed

> now going to probelm 3: Build the Campus Custom website
>
> scaffold a react + vite + typescript front end for campus customs. put a nav bar at the
> top that links to the main pages: home, products, about us, log in, create account.
>
> pull campus customs style wording from yalebulldogblue.com for home and about us, but
> write these pages in "your own voice without copying the original site text directly".
>
> on the products page, show product imagees from the catalogue using the image paths in
> the database with basic product info inlcuding "name, price, and short description."
>
> make each product open a single item page with a large image on one side and full
> product text on the other including description, price, and sizes/stock when you have
> them... clicking a card on products should take the shopper directly there.
>
> add a chat interface in the bottom right of the site, and a floating chat panel is fine.
> it does not need to talk to an agent yet, so a stub that will call your backend later is
> enough for this problem.
>
> and a small API will be needed soon to read the datavase. it is okay to start a simple
> Fast API app in backend/main.py just to serve products and images, then grow it into the
> agent backend in problem 5!

### Follow-up prompt

No follow-up prompt was needed; the first prompt was sufficient. It listed the exact stack,
the five nav destinations, the sourcing rule for the Home and About Us copy, the three
fields required on a product card, the two-column layout and contents of the single-item
page, the click-through behaviour, the placement and allowed scope of the chat stub, and
the file the API should live in — so the site was built, type-checked and verified in the
browser in one pass, with the only judgement call (matching the project's light-pink theme
to Yale navy) made without needing to ask.

---

## Problem 4 — Create Account and Login

Build a normal sign-up and sign-in flow that writes new accounts to the `users` table with
securely hashed passwords, confirm the seeded test user and a brand new account both work,
and document how auth works in `output/harness.md`.

### Prompt I typed

> now going to problem 4: Create account and login:
>
> i need to build a normal create account and login flow.
>
> * create account: include first name, last name, email, and password (confirm password
>   is a nice touch too).
> * login: use email and password.
> * new accounts should go into the users table, and make sure to store passwords securely
>   so hackers cannot access them.
> * the seed database already has a test user with email "test@campuscustoms.yale.edu" and
>   password "password".
> * confirm that you can log in as that user, and also that a brand new account created
>   works as well.
>
> finally, update output/harness.md with how auth works, including what you store for a
> user and how passwords are protected.

### Follow-up prompt

No follow-up prompt was needed; the first prompt was sufficient. It named every field on
the sign-up form, the login credentials, the destination table, the security requirement,
the exact seeded account to test against, both confirmations to run, and the documentation
to update — so the coder recovered the seed data's PBKDF2 iteration count (120,000) by
matching the known test password against the stored digest, reused that identical scheme
for new accounts so seeded and new rows verify through one code path, and confirmed both
logins through the running website rather than only through the API.

---

## Problem 5 — PydanticAI Agent Backend

Build the shop chatbot as a PydanticAI agent behind FastAPI, split across `prompts/prompt.md`,
`agent.py`, `tools.py` and `models.py`, wired to the front-end chat widget, and runnable with
`uvicorn main:app --reload --port 8000` from the `backend/` folder.

### Prompt I typed

> and going for Problem5: PydanticAI agent backend
>
> build the shop chatbot as a PydanticAI agent behind FastAPI, plugged into your front-end
> chat widget. put the api app in `backend/main.py` which is the file you run with Uvicorn.
> keep the agent as these four files next to it:
>
> * `backend/prompts/prompt.md` — system prompt (grow this same file later)
> * `backend/agent.py` — agent entry / wiring
> * `backend/tools.py` — tools the agent can call
> * `backend/models.py` — pydantic / pydanticai structured types
>
> in `main.py`, expose a chat route so a message from the website returns a reply from the
> agent (and whatever else you need for products/auth). you will need your ai model api key
> for the agent.
> and put campus customs voice and safety basics into `prompts/prompt.md` (you will expand
> tools and safety later). and start or update types in `models.py` for chat replies /
> product cards as needed.
> in `output/harness.md`, note how the front end talks to fastapi and how the agent is
> loaded (prompt file + model).
> make sure the backend runs from the `backend/` folder like this: uvicorn main:app --reload
> --port 8000

### Follow-up prompt

No follow-up prompt was needed; the first prompt was sufficient. It named the four agent
files and their individual responsibilities, kept `main.py` as the Uvicorn entry point,
specified the chat route contract, said where the voice and safety rules belong, named what
to document in the harness, and gave the exact run command — which was the detail that
mattered most, since running from `backend/` meant the modules had to import each other
flatly rather than as a `backend.` package. The one problem found during this step was
caught by self-testing rather than by a follow-up prompt: a live question about the
Harvard–Yale t-shirt returned "no match" because a single SQL `LIKE` could not match
"t-shirt" against the stored name "T Shirt", so catalogue search was rewritten to score
products on normalized, tokenized query words before the work was handed over.

---

## Problem 6 — Tools: Product Info and Stock

Give the agent tools that read real product descriptions, prices and stock-by-size from
`campus_customs.db`, expand the prompt so it calls them for price and stock questions, add
the return types to `models.py`, and document each tool and its chosen fields in the harness.

### Prompt I typed

> now going to problem 6: tools: product info and stock
> give the agent tools that look up real information from `campus_customs.db` :
>
> * product description
> * price
> * how many are in stock (by size when the customer asks)
>
> the agent must use the database, so it should not invent prices or quantities. if a size
> is out of stock, you say so clearly.
> expand `prompts/prompt.md` so the agent knows to call these tools for price and stock
> questions. aand add or update return types in `models.py`.
> in `output/harness.md`, list each tool and explain which model fields you chose for
> lookup results and why.

### Follow-up prompt

No follow-up prompt was needed; the first prompt was sufficient. It named the three lookups
to cover, stated the non-negotiable rule (use the database, never invent prices or
quantities), called out the sold-out case explicitly, and named all three files to
update — including the requirement to *justify* the field choices, which is what pushed the
return types beyond raw numbers into fields that exist specifically to prevent a wrong
restatement: a pre-formatted `price_display` so a price cannot be reformatted into "$68" or
"about seventy", all six sizes returned including the zeros so a sold-out size cannot be
quietly omitted, `other_sizes_in_stock` so the honest answer does not cost a second tool
call, and an `availability_note` sentence composed in Python so the risky step of turning
six quantities into one claim happens in testable code rather than in the model.

---

## Problem 7 — Chat Search That Updates the Page

Make the agent's catalogue matches appear on the website as product cards with image, name,
price and short info, keep the Problem 3 single-item page working for those chat-placed
cards, and document in the prompt and the harness how search results reach the page.

### Prompt I typed

> now going to problem 7: Chat search that updates the page
>
> add a feature to the site where if a customer asks about a type of item like "what
> hoodies do you have?", the agent searches the catalogue and the website dynamically shows
> those matching items as product cards with image, name, price, and short info.
>
> this is an api contract where the agent returns structured product matches and the front
> end renders them on the website.
>
> after the dynamic product cards are loaded, make sure the same single-item page behavior
> built in problem 3 still works, so each product card including the ones put on the page
> by chat opens that detail view with large image and full info when clicked.
>
> update prompts/prompt.md and output/harness.md so it is clear how search results reach
> the page.

### Follow-up prompt

No follow-up prompt was needed; the first prompt was sufficient. It gave the triggering
example, the four fields each card must show, the framing as an API contract between agent
and front end, the requirement that chat-placed cards behave like catalogue cards, and both
files to document — which together settled the two design decisions: the chat results were
lifted into a provider above the router so the same match set renders both inside the chat
panel and as a strip on the Products page, and the existing `ProductCard` component was
reused rather than a new chat-specific card being written, so a card Bailey places on the
page opens the Problem 3 detail view through the same route with no extra wiring.

---

## Problem 8 — Customer Memory

Save logged-in shoppers' chat history in the database and reload it when they return, give
the agent the customer's identity through its deps, pass page context so "do you have this
in pink?" resolves to the product on screen, keep guest chat working without persistence,
and document all three in the harness.

### Prompt I typed

> now going to problem 8: customer memory
>
> when a shopper is logged in, save their chat history in the database in an appropriate
> table and reload it when they return. the agent should know who is chatting (by name,
> email) — put that in agent deps (or an equivalent clear pattern) and/or tools the agent
> can call.
>
> also pass enough page context that if someone is on a product page and asks "do you have
> this in pink?", the agent knows which item they mean. hint: you can put code into the
> agent context.
>
> guests can still chat, but history only needs to persist for logged-in users... document
> in output/harness.md: how user chat history is stored, what customer fields the agent
> sees, and how page context is passed!

### Follow-up prompt

No follow-up prompt was needed; the first prompt was sufficient. It named the table to use,
the reload requirement, the deps pattern for customer identity, the exact "do you have this
in pink?" scenario to make work, the guest rule, and the three things to document — which
together determined the design: identity is resolved from the database by `user_id` so a
browser cannot claim to be another customer, stored turns are replayed as message history
with only their text so old prices cannot be reused as current, and a browser-supplied
`product_id` is validated against the catalogue before it reaches the agent. Two real
search bugs surfaced during self-testing rather than from a follow-up prompt: the agent
reported "two crewnecks under $60" when there are 28, because search returned a capped list
with no total, and the underlying cause was that the word "under" matched the brand "Under
Armour" as a substring while "60" matched nothing yet still raised the match threshold.
Both were fixed — a `SearchResults` envelope carrying `total_matches`/`truncated`, dropping
query words that match no product, and parsing price phrases into real numeric bounds —
before the work was handed over.

---

## Problem 9 — Usability Improvements

Choose and implement two front-end and two agent/backend improvements, write
`output/usability.md` before or as the work is built saying what was added and why it helps,
and make sure every improvement actually shows up in the running app.

### Prompt I typed

> now going to problem 9: usability improvements
> now that the core shop works, improve it. choose and implement:
>
> * 2 front-end usability improvements
> * 2 agent / backend usability improvements
>
> front-end improvements are things that make the site look better and make it easier to
> use. and agent / backend improvements are things that make the agent output better, more
> accurate, or safer. these could be new agent tools or things that make the agent run
> faster or cheaper.
>
> write `output/usability.md` "before or as" you build. for each of the improvements, say:
>
> * what you added
> * why it helps a campus customs shopper or the business
>
> then make sure all improvements actually show up in the running app. * noted that graders
> will read the write-up and look for the features. it has to be aligned. i want the
> improvements should be good and well organized

### Follow-up prompt

No follow-up prompt was needed; the first prompt was sufficient. It fixed the count and the
split of improvements, defined what counts as a front-end versus an agent improvement, gave
the two things each write-up entry must state, required the features to be real in the
running app, and warned that graders would check the write-up against the app — so
`output/usability.md` was written first as a plan, each improvement was then verified in the
browser or against the database, and every claim in the document was replaced with a
measured result (size counts checked against `inventory`, cache timings over 200 calls, and
a quoted live chat reply). Two things were caught by that self-check rather than by a
follow-up prompt: the size-filter summary line read "Showing size XS matching size XS"
because the size was templated twice, and Escape-to-close did not return keyboard focus
because the launcher button is only mounted after the panel closes, making the ref null
inside the key handler. Both were fixed before the work was handed over.

---

## Problem 10 — Style the Website

Add an imaginative, high-end design system — blush palette with rose-slate contrast, Syne
and Plus Jakarta Sans typography, 3D card tilt and floating live stock badges, a
glassmorphism chat widget, and a dynamic interactive hero — then document it in
`output/design.md`.

### Prompt I typed

> now going to problem 10: style the website
> add an imaginative, high-end, and innovative design system so the site feels like a
> modern, luxury campus customs storefront:
>
> * color palette: soft lightpink (`#fde8ed`) base background with sophisticated
>   rose-slate contrast (`#1e293b` text, `#8b5cf6` subtle accents), giving it a chic
>   aesthetic while ensuring high-contrast readability
> * typography: dynamic pairing using plus jakarta sans for crisp body copy and
>   syne/clash display for high-fashion headline hierarchy
> * product presentation & motion: interactive 3d-card tilt effect on hover, smooth
>   micro-interactions, floating stock badges with live availability indicators, and
>   polished quick-view transitions
> * chat interface feel: glassmorphism floating widget with smooth backdrop-blur, custom
>   pulsing active status, ambient micro-glow, and animated typing indicators
> * innovative features: dynamic hero banner with interactive campus merchandise showcases
>   and seamless layout transitions that drive higher engagement
>
> write `output/design.md` detailing what you changed and why it helps customers stick
> around and buy, keeping the explanation concrete, persuasive, and concise

### Follow-up prompt

No follow-up prompt was needed; the first prompt was sufficient. It specified the exact hex
values, the font pairing, and each of the five feature areas by name, plus the requirement
that the write-up be concrete and tie back to buying — so the palette went into a single
token block and the measured contrast was reported (12.50:1 body text, AAA) rather than
merely claimed, the tilt and hero were built as reusable components that honour
`prefers-reduced-motion` in both CSS and JavaScript, and every visual claim in
`output/design.md` was confirmed against computed styles in the running app. One verification
obstacle was worth recording: the Browser pane reports `document.hidden = true`, so Chrome
pauses `requestAnimationFrame` and the tilt cannot paint there; the tilt maths was therefore
confirmed by running its rAF callback synchronously, which exercises the identical code path
a visible tab takes.

---

## Problem 11 — Site Testing (App Check)

Test the live site and document it in `output/app_check.html` with screenshots and short
captions for three checks: chat reading real inventory, dynamic search-result cards after a
category question, and one Problem 9 usability feature.

### Prompt I typed

> now going to problem 11: site testing (app check)
> test the live site and document it in `output/app_check.html` (a page you can
> double-click open). include clear screenshots and short captions for:
>
> 1. chat checking the inventory level of an item :honest stock/price from the db
> 2. the dynamic search-result cards appearing after a category question :e.g. hoodies
> 3. one of the usability features you added in problem 9
>
> make the html easy to grade: heading for each check, screenshot, and one or two accurate
> and detailed sentences on what the screenshot proves. put the screenshot image files in
> `output/app_check_images/` and link them from `app_check.html` with relative paths (for
> example `app_check_images/inventory.png`).

### Follow-up prompt

No follow-up prompt was needed; the first prompt was sufficient. It named the three checks,
the output file, the folder and relative-path convention for the images, and the exact
structure each section needed — heading, screenshot, and one or two accurate sentences on
what the screenshot proves — so the page was built to be graded at a glance, with each
claim backed by a comparison table between what the screenshot shows and what the database
actually holds. Two capture details were handled during the work rather than by asking: the
Browser pane had collapsed to a 0×0 viewport so nothing rendered until an explicit 1280×900
viewport was set, and the first check was deliberately staged on the Basic Hoodie product
page so the page's own size tiles and the agent's per-size answer appear in the same frame,
which lets a grader confirm the agreement without taking anything on trust.

---

## Problem 12 — Audit Trail, Safety, Finish Harness

Keep an append-only `output/audit_trail.json` of agent-loop activity that is never wiped
between runs, add safety rules to `prompts/prompt.md`, and finish `output/harness.md` so the
model fields, tools, safety rules and specs are all documented.

### Prompt I typed

> now going to problem 12: audit trail, safety, finish harness
> keep an append-only `output/audit_trail.json` of agent-loop activity (time, tool name,
> short args/result, stop reason). do not wipe it between runs!
> also, think of some safety rules and put them in `prompts/prompt.md`.
> finish `output/harness.md` so it is clear how the system works:
>
> * model fields in `models.py` and why you chose them
> * tools and abilities
> * safety rules
> * specs :loop limits, result caps, models, how to run front + back

### Follow-up prompt

No follow-up prompt was needed; the first prompt was sufficient. It named the file, the four
fields each record needs, the non-negotiable append-only requirement, and the four harness
sections to complete — so the trail was built with one wrapper that every tool passes
through (so the record cannot drift from what the agent actually did), atomic `os.replace`
writes behind a lock, a corrupt trail moved aside rather than deleted, and swallowed logging
failures so auditing can never take the shop down. The invitation to "think of some safety
rules" was taken as the open-ended part of the task and answered with eight grouped rules
covering false price claims from shoppers, promises the shop cannot honour, refusing
sensitive data, customer isolation, prompt-injection and treating catalogue text as data,
staying out of medical and legal territory, de-escalation, and admitting uncertainty. The
trail then paid for itself during self-testing rather than needing a follow-up prompt: a
normal question started returning `502` with tool calls logged but no `run_end`, which
located the fault in the post-run block — `result.usage()` called as a method when `usage`
is a property on `AgentRunResult` — and that block is now inside the guard so the same class
of failure would be recorded as `agent_error`.

---

## Problem 13 — *(pending)*

*This section will be filled in when Problem 13 is assigned.*
