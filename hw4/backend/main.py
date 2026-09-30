"""Campus Customs API — the app you run with Uvicorn.

Serves the catalogue and product images, handles accounts, and puts the PydanticAI shop
agent behind POST /api/chat.

Run from the backend folder:

    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import agent as shop_agent
import audit
import auth
import db
from models import (
    AuthResponse,
    CatalogueStats,
    ChatDeps,
    ChatHistoryMessage,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    LoginRequest,
    PageContext,
    Product,
    PublicUser,
    SignupRequest,
)

logger = logging.getLogger("campus_customs")

app = FastAPI(
    title="Campus Customs API",
    description="Catalogue, accounts and the shop agent for the Campus Customs storefront.",
    version="0.5.0",
)

# The Vite dev server runs on 5173 and proxies to us, but allow it directly too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Product photos live outside the repo (data/ is gitignored) and are served from disk.
if db.PRODUCT_IMAGE_DIR.exists():
    app.mount("/media", StaticFiles(directory=db.DATA_DIR), name="media")


# ---------------------------------------------------------------------------- catalogue


@app.get("/api/health")
def health() -> dict[str, object]:
    """Confirms the API is up, the database is readable, and the agent can be built."""
    try:
        stats = db.catalogue_stats()
    except Exception as exc:  # pragma: no cover - surfaced in the UI as a banner
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}")
    return {
        "status": "ok",
        "database": db.DB_PATH.name,
        "agent_model": shop_agent.tools.DEFAULT_MODEL,
        "agent_key_loaded": bool(shop_agent.tools.PORTKEY_API_KEY),
        "catalogue_cache": db.cache_status(),
        "audit_trail": audit.stats(),
        **stats,
    }


@app.get("/api/stats", response_model=CatalogueStats)
def stats() -> CatalogueStats:
    """Catalogue headline numbers for the home page."""
    return CatalogueStats(**db.catalogue_stats())


@app.get("/api/products", response_model=list[Product])
def get_products(
    search: str | None = Query(default=None, description="Free text over name, description, colors and tags"),
    garment_type: str | None = Query(default=None, description="Loose match on garment type"),
    limit: int | None = Query(default=None, ge=1, le=200),
) -> list[Product]:
    """The browsable catalogue, with optional filters."""
    return [Product(**row) for row in db.list_products(search, garment_type, limit)]


@app.get("/api/garment-types", response_model=list[str])
def get_garment_types() -> list[str]:
    """Distinct garment types, used for the filter chips on the products page."""
    return db.list_garment_types()


@app.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: str) -> Product:
    """One product with description, price and stock for every size."""
    row = db.get_product(product_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No product named {product_id!r}")
    return Product(**row)


# ----------------------------------------------------------------------------- accounts


@app.post("/api/signup", response_model=AuthResponse, status_code=201)
def signup(request: SignupRequest) -> AuthResponse:
    """Create an account.

    The plaintext password exists only for the length of this function: it is turned into
    a salted PBKDF2 digest and the plaintext is never stored, logged or echoed back.
    """
    email = auth.normalize_email(request.email)

    complaint = auth.password_problem(request.password)
    if complaint:
        raise HTTPException(status_code=422, detail=complaint)

    # users.email is UNIQUE, so check first to return a friendly 409 instead of a 500.
    if db.email_taken(email):
        raise HTTPException(
            status_code=409,
            detail="That email already has an account. Try logging in instead.",
        )

    user = db.create_user(
        first_name=request.first_name.strip(),
        last_name=request.last_name.strip(),
        email=email,
        password_hash=auth.hash_password(request.password),
    )
    return AuthResponse(
        user=PublicUser(**user),
        message=f"Welcome to Campus Customs, {user['first_name']}!",
    )


@app.post("/api/login", response_model=AuthResponse)
def login(request: LoginRequest) -> AuthResponse:
    """Sign in with email and password.

    A wrong email and a wrong password produce the same 401 and the same wording, so the
    response cannot be used to discover which addresses have accounts.
    """
    row = db.find_user_by_email(auth.normalize_email(request.email))

    # Hash against a throwaway digest when the email is unknown, so both failure modes
    # take the same time and the endpoint cannot be used to enumerate accounts.
    stored = row["password_hash"] if row is not None else auth.DUMMY_HASH
    if not auth.verify_password(request.password, stored) or row is None:
        raise HTTPException(status_code=401, detail="That email and password do not match.")

    user = db.public_user(row)
    greeting = user["first_name"] or user["name"]
    return AuthResponse(user=PublicUser(**user), message=f"Welcome back, {greeting}!")


# --------------------------------------------------------------------------------- chat


def _build_deps(request: ChatRequest) -> tuple[ChatDeps, bool]:
    """Assemble the agent's context: who is chatting, and where they are.

    Identity is looked up in the database from `user_id`. Nothing about the shopper is
    taken from the request body, so a browser cannot claim to be another customer by
    editing a name or email field. Returns the deps and whether the shopper is signed in.
    """
    context = request.page_context or PageContext()

    # Where they are. A product_id from the browser is resolved against the catalogue, so
    # an unknown or made-up id simply produces no page context rather than a bad answer.
    current_product_id: str | None = None
    current_product_name: str | None = None
    if context.product_id:
        row = db.get_product(context.product_id)
        if row is not None:
            current_product_id = row["product_id"]
            current_product_name = row["name"]

    deps = ChatDeps(
        page=context.page,
        path=context.path,
        current_product_id=current_product_id,
        current_product_name=current_product_name,
        search=context.search,
        garment_type=context.garment_type,
    )

    # Who they are.
    if request.user_id is not None:
        user = db.get_user_by_id(request.user_id)
        if user is not None:
            deps.user_id = int(user["id"])
            deps.first_name = user["first_name"] or user["name"]
            deps.full_name = user["name"]
            deps.email = user["email"]
            deps.is_logged_in = True

    return deps, deps.is_logged_in


@app.get("/api/chat/history", response_model=ChatHistoryResponse)
def chat_history(user_id: int = Query(..., description="The signed-in shopper's id")) -> ChatHistoryResponse:
    """Reload a signed-in shopper's saved conversation.

    Guests have no history to return: nothing is stored for them, so there is nothing to
    look up. A `user_id` that does not exist is a 404 rather than an empty conversation,
    so a stale browser session is visible instead of silently looking like a new shopper.
    """
    if db.get_user_by_id(user_id) is None:
        raise HTTPException(status_code=404, detail="No such account.")

    messages = [
        ChatHistoryMessage(
            id=row["id"],
            role=row["role"],
            content=row["content"],
            products=[Product(**product) for product in row["products"]],
            created_at=row["created_at"],
        )
        for row in db.get_chat_history(user_id)
    ]
    return ChatHistoryResponse(user_id=user_id, messages=messages)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """One shopper turn, answered by the PydanticAI agent.

    For a signed-in shopper, both sides of the turn are written to `chat_messages`, and
    their earlier turns are replayed into the agent so the conversation continues across
    visits. Guests get the same answers with nothing stored.
    """
    message = request.message.strip()
    run_id = audit.new_run_id()
    if not message:
        # Rejected before the model is called, but still recorded - a turn that produced
        # no answer should be visible in the trail, not missing from it.
        audit.log_run_end(run_id, "empty_message")
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    deps, logged_in = _build_deps(request)
    deps.run_id = run_id

    # Past turns, so the agent remembers the conversation. Read before the new message is
    # saved, so the current turn is not duplicated as both history and prompt.
    history = db.get_chat_history(deps.user_id) if logged_in else None

    try:
        reply, products = await shop_agent.answer(message, deps=deps, history=history)
    except Exception as exc:
        # Log the cause for us, but never leak model or key details to the browser.
        logger.exception("Agent run failed")
        raise HTTPException(
            status_code=502,
            detail="Bailey could not answer just now. Please try again in a moment.",
        ) from exc

    saved = False
    if logged_in and deps.user_id is not None:
        # Persist only after a successful answer, so a failed turn does not leave a
        # question in the transcript with no reply after it.
        db.save_chat_message(deps.user_id, "user", message)
        db.save_chat_message(
            deps.user_id,
            "assistant",
            reply,
            [product.model_dump() for product in products] or None,
        )
        saved = True

    return ChatResponse(reply=reply, products=products, saved=saved)
