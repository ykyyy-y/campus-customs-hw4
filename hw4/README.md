# Campus Customs

A customer storefront for **Campus Customs**, the Yale apparel shop at 57 Broadway in New
Haven, with a shop assistant that answers from the store's real catalogue.

- **Front end** — React + Vite + TypeScript
- **Back end** — FastAPI
- **Agent** — PydanticAI, reaching OpenAI through the Portkey gateway
- **Data** — a local SQLite catalogue; every price and stock number the site or the
  chatbot states is read from it

Shoppers can browse 102 products, create an account, chat about merchandise, watch matching
items appear on the page as they ask, and get honest answers about price and availability.

---

## What is not in this repository

Three things are deliberately excluded by `.gitignore` and must be supplied locally:

| Excluded | Why |
|---|---|
| `.env` | Contains a real API key. Use `.env.example` as the template. |
| `data/campus_customs.db` | The provided database is not redistributed. |
| `data/products/*.jpg` | The 102 product photos are not redistributed. |

---

## Setup

### 1. Put the data pack in place

Unzip the provided data pack into this folder so it looks like this:

```
hw4/
└── data/
    ├── campus_customs.db
    └── products/
        ├── 2025-yale-vs-harvard-t-shirt.jpg
        └── ... (102 .jpg files)
```

If your archive extracts to a nested `data/data/`, flatten it — the database must be at
`hw4/data/campus_customs.db` and the images at `hw4/data/products/`.

### 2. Add your API key

```bash
cp .env.example .env
```

Then edit `.env` and set `PORTKEY_API_KEY` to your own key.

### 3. Install the backend

From the `hw4/` folder:

```bash
python -m venv .venv
```

```bash
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

On macOS or Linux use `.venv/bin/python` instead of `.venv/Scripts/python.exe`.

### 4. Install the front end

```bash
cd frontend && npm install
```

---

## Running it

Two servers, two terminals.

**Back end** — from `hw4/backend/`:

```bash
uvicorn main:app --reload --port 8000
```

**Front end** — from `hw4/frontend/`:

```bash
npm run dev
```

Then open **http://localhost:5173**.

Vite proxies `/api` and `/media` through to the backend on port 8000, so the browser only
ever talks to one origin.

### Check it came up correctly

```bash
curl http://localhost:8000/api/health
```

A healthy response reports `102` products, the agent model, and `agent_key_loaded: true`.
If `agent_key_loaded` is `false`, the `.env` key was not picked up. If the database is
missing you get a `503` naming the path it expected.

### Signing in

The provided database ships with a test account:

- **Email** `test@campuscustoms.yale.edu`
- **Password** `password`

Or create a new account from the site — it writes a real row to the `users` table with a
salted PBKDF2 password hash.

---

## Layout

```
hw4/
├── AI_prompts.md          every prompt used to build this, one section per problem
├── requirements.txt       Python dependencies
├── .env.example           template for the API key
├── .gitignore
├── README.md
├── frontend/              Vite React TypeScript app
├── backend/               FastAPI app
│   ├── main.py            the app you run with uvicorn; owns every HTTP route
│   ├── agent.py           agent entry and wiring
│   ├── models.py          Pydantic types shared by the API and the agent
│   ├── tools.py           the tools the agent can call, plus the model wiring
│   ├── db.py              SQLite reads and writes
│   ├── auth.py            password hashing
│   ├── audit.py           append-only agent audit trail
│   └── prompts/
│       └── prompt.md      the system prompt: shop voice and safety rules
└── output/
    ├── harness.md         how the whole system works
    ├── design.md          the design system and why it helps the shop
    ├── usability.md       four usability improvements, with measurements
    ├── app_check.html     live-site test report — open this in a browser
    ├── app_check_images/  screenshots linked from app_check.html
    └── audit_trail.json   append-only record of agent activity
```

**The agent is four files**: `prompts/prompt.md`, `agent.py`, `tools.py` and `models.py`.
`db.py`, `auth.py` and `audit.py` sit alongside them as the data, password and logging
layers the app needs to run.

---

## How it works, briefly

- **The catalogue is the only authority.** The agent has no product knowledge of its own.
  Ten tools read SQLite, and the prompt requires a fresh lookup for every price and stock
  question.
- **The agent returns product *ids*, never product objects.** The server re-reads each id
  from the database to build the cards, so a card cannot carry a price the model invented.
- **Chat results become page state.** Matching items render as cards inside the reply *and*
  as a strip on the Products page, and every card opens the same product detail view.
- **Signed-in shoppers get memory.** Their conversation is saved to `chat_messages` and
  replayed when they return — text only, so an old price is never reused as current.
- **Identity comes from a session token, never from the request.** Logging in issues a
  256-bit random token (only its SHA-256 is stored) which the browser returns as
  `Authorization: Bearer …`. Chat and history requests carry no user id, so one shopper
  cannot read or write another's conversation.
- **Page context travels with each message**, so "do you have this in pink?" on a product
  page resolves to that product.
- **Every agent turn is audited** to `output/audit_trail.json`: tool calls, short arguments
  and results, timings and a stop reason. The file is append-only and is never wiped.

Full detail, including the model-field rationale, loop limits and safety rules, is in
[`output/harness.md`](output/harness.md).
