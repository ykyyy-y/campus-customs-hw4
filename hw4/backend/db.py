"""SQLite access for the Campus Customs storefront.

Every price and every stock number the site shows comes from here. Nothing about a
product is invented anywhere else in the app.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

# backend/db.py -> HW 4/ -> HW 4/data/campus_customs.db
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
PRODUCT_IMAGE_DIR = DATA_DIR / "products"

MEDIA_URL_PREFIX = "/media"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]


# --------------------------------------------------------------------- read cache
#
# The catalogue and inventory are read-only for the life of a shopping session: 102
# products and 612 stock rows that no request writes to. Every tool call used to re-open
# SQLite, re-run the join and re-parse the JSON `colors`/`search_tags` columns for all 102
# rows, and one chat turn makes several tool calls. Building the rows once and reusing
# them makes a turn measurably faster and cheaper.
#
# Writes (users, chat_messages) are never cached, and the TTL plus invalidate_cache()
# means a stock edit is still picked up.

CACHE_TTL_SECONDS = float(os.getenv("CAMPUS_CUSTOMS_CACHE_TTL", "300"))
_cache_products: list[dict[str, Any]] | None = None
_cache_by_id: dict[str, dict[str, Any]] = {}
_cache_loaded_at: float = 0.0
_cache_hits = 0
_cache_misses = 0


def invalidate_cache() -> None:
    """Drop the cached catalogue so the next read rebuilds it from SQLite."""
    global _cache_products, _cache_by_id, _cache_loaded_at
    _cache_products = None
    _cache_by_id = {}
    _cache_loaded_at = 0.0


def cache_status() -> dict[str, Any]:
    """Cache state, surfaced on /api/health."""
    return {
        "cached_products": len(_cache_products) if _cache_products else 0,
        "age_seconds": round(time.monotonic() - _cache_loaded_at, 1) if _cache_products else None,
        "ttl_seconds": CACHE_TTL_SECONDS,
        "hits": _cache_hits,
        "misses": _cache_misses,
    }


def _all_products() -> list[dict[str, Any]]:
    """Every product with its inventory, from cache when warm."""
    global _cache_products, _cache_by_id, _cache_loaded_at, _cache_hits, _cache_misses

    fresh = (
        _cache_products is not None
        and (time.monotonic() - _cache_loaded_at) < CACHE_TTL_SECONDS
    )
    if fresh and _cache_products is not None:
        _cache_hits += 1
        return _cache_products

    _cache_misses += 1
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        inventory = _inventory_by_product(conn, [row["product_id"] for row in rows])
        products = [
            _row_to_product(row, inventory.get(row["product_id"], [])) for row in rows
        ]
    finally:
        conn.close()

    _cache_products = products
    _cache_by_id = {product["product_id"]: product for product in products}
    _cache_loaded_at = time.monotonic()
    return products


def get_connection() -> sqlite3.Connection:
    """Open a read-oriented connection with dict-like rows."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. The .db file is not committed to git - "
            "unzip data.zip into HW 4/data/ before running the backend."
        )
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_json_list(raw: Any) -> list[str]:
    """`colors` and `search_tags` are stored as JSON-encoded strings, not lists."""
    if isinstance(raw, list):
        return raw
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return [part.strip() for part in str(raw).split(",") if part.strip()]
    return value if isinstance(value, list) else [str(value)]


def _size_sort_key(size: str) -> tuple[int, str]:
    """Sort XS < S < M < L < XL < XXL instead of alphabetically."""
    try:
        return (SIZE_ORDER.index(size), size)
    except ValueError:
        return (len(SIZE_ORDER), size)


def image_url_for(image_file_path: str) -> str:
    """`products/foo.jpg` (stored) -> `/media/products/foo.jpg` (served)."""
    return f"{MEDIA_URL_PREFIX}/{str(image_file_path).lstrip('/')}"


def _row_to_product(row: sqlite3.Row, inventory: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the single product shape used by the API, the UI, and later the agent."""
    inventory = sorted(inventory, key=lambda item: _size_sort_key(item["size"]))
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": _parse_json_list(row["colors"]),
        "search_tags": _parse_json_list(row["search_tags"]),
        "image_file_path": row["image_file_path"],
        "image_url": image_url_for(row["image_file_path"]),
        "price": float(row["price"]),
        "inventory": inventory,
        "total_stock": sum(int(item["quantity"]) for item in inventory),
        "sizes_in_stock": [
            item["size"] for item in inventory if int(item["quantity"]) > 0
        ],
    }


def _inventory_by_product(
    conn: sqlite3.Connection, product_ids: list[str]
) -> dict[str, list[dict[str, Any]]]:
    """One query for all sizes, so listing 102 products stays a 2-query page."""
    if not product_ids:
        return {}
    placeholders = ",".join("?" for _ in product_ids)
    rows = conn.execute(
        f"SELECT product_id, size, quantity FROM inventory "
        f"WHERE product_id IN ({placeholders})",
        product_ids,
    ).fetchall()
    grouped: dict[str, list[dict[str, Any]]] = {pid: [] for pid in product_ids}
    for row in rows:
        grouped[row["product_id"]].append(
            {"size": row["size"], "quantity": int(row["quantity"])}
        )
    return grouped


# Words that carry no signal in a shopper's phrasing ("do you have a hoodie in navy").
_STOPWORDS = {
    "a", "an", "and", "any", "are", "as", "at", "be", "do", "does", "for", "got",
    "have", "in", "is", "it", "me", "my", "of", "on", "or", "show", "some", "that",
    "the", "their", "there", "they", "this", "to", "want", "was", "we", "what",
    "with", "you", "your",
}


def _normalize(text: str) -> str:
    """Lowercase and turn every non-alphanumeric run into a single space.

    This is what lets "t-shirt" match the stored name "T Shirt", and "1/4 zip" match
    "1 4 Zip".
    """
    return " ".join("".join(c if c.isalnum() else " " for c in text.lower()).split())


def _tokens(text: str) -> list[str]:
    """Meaningful search words, de-duplicated, order preserved."""
    seen: set[str] = set()
    out: list[str] = []
    for word in _normalize(text).split():
        if word in _STOPWORDS or word in seen:
            continue
        seen.add(word)
        out.append(word)
    return out


def _token_matches(token: str, haystack: str) -> bool:
    """Match a token against normalized text, tolerating simple plurals."""
    if token in haystack:
        return True
    # "hoodies" should find "hoodie"; "tee" should not be forced to match "tees" only.
    singular = token[:-1] if token.endswith("s") and len(token) > 3 else None
    if singular and singular in haystack:
        return True
    return f"{token}s" in haystack


_UNDER_WORDS = r"(?:under|below|less than|cheaper than|up to|max|at most)"
_OVER_WORDS = r"(?:over|above|more than|at least|from)"


def extract_price_filter(search: str) -> tuple[str, float | None, float | None]:
    """Pull "under $60" style phrases out of a query and return them as bounds.

    Shoppers ask for price ranges in words, and those words are a trap for a text search:
    "crewnecks under $60" contains the token "under", which happens to match the brand
    "Under Armour" and quietly narrows the results to two Under Armour crewnecks. Parsing
    the phrase into a real numeric bound fixes the wrong answer and adds the filter the
    shopper actually wanted.

    Returns the query with the price phrase removed, plus (max_price, min_price).
    """
    text = search
    max_price: float | None = None
    min_price: float | None = None

    under = re.search(rf"{_UNDER_WORDS}\s*\$?\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if under:
        max_price = float(under.group(1))
        text = text[: under.start()] + " " + text[under.end() :]

    over = re.search(rf"{_OVER_WORDS}\s*\$?\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if over:
        min_price = float(over.group(1))
        text = text[: over.start()] + " " + text[over.end() :]

    return text.strip(), max_price, min_price


def list_products(
    search: str | None = None,
    garment_type: str | None = None,
    limit: int | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
) -> list[dict[str, Any]]:
    """All products, optionally narrowed by free text or garment type.

    Free text is scored in Python rather than matched as one SQL `LIKE` phrase. A single
    `LIKE '%...%'` needs the shopper's words to appear verbatim and in order, which fails
    on real phrasing: "2025 Yale vs Harvard t-shirt" never matches the stored name
    "2025 Yale Vs Harvard T Shirt" because of the hyphen. Instead the query is split into
    words and each product is scored by how many of them it contains, across its name,
    description, colours, search tags and garment type. The catalogue is 102 rows, so
    scoring every row costs nothing.
    """
    # A price phrase inside the free text becomes a numeric bound, not a search word.
    if search:
        search, phrase_max, phrase_min = extract_price_filter(search)
        max_price = max_price if max_price is not None else phrase_max
        min_price = min_price if min_price is not None else phrase_min

    products = _all_products()

    if garment_type:
        # garment_type has 22 near-duplicate spellings, so match loosely.
        needle = garment_type.strip().lower()
        products = [p for p in products if needle in p["garment_type"].lower()]

    if max_price is not None:
        products = [p for p in products if p["price"] <= max_price]
    if min_price is not None:
        products = [p for p in products if p["price"] >= min_price]

    query_tokens = _tokens(search) if search else []
    if query_tokens:
        haystacks = {
            product["product_id"]: _normalize(
                " ".join(
                    [
                        product["name"],
                        product["garment_type"],
                        product["description"],
                        " ".join(product["colors"]),
                        " ".join(product["search_tags"]),
                    ]
                )
            )
            for product in products
        }

        # Drop words that match nothing in the catalogue before scoring. A shopper asking
        # for "crewnecks under $60" contributes the useful token "crewnecks" plus the
        # noise tokens "under" and "60"; counting the noise would raise the bar to 2 of 3
        # words and throw away every crewneck that simply does not contain the word
        # "under". Only words the catalogue actually knows about get a vote.
        useful = [
            token
            for token in query_tokens
            if any(_token_matches(token, hay) for hay in haystacks.values())
        ]
        if not useful:
            # No searchable word survived - "a gift under $40" has no catalogue word in
            # it. If a price bound was given, that alone is still a real filter, so
            # return what fits the budget instead of nothing.
            if max_price is None and min_price is None:
                return []
            return products[: int(limit)] if limit else products

        scored: list[tuple[int, str, dict[str, Any]]] = []
        for product in products:
            haystack = haystacks[product["product_id"]]
            score = sum(1 for token in useful if _token_matches(token, haystack))
            if score:
                scored.append((score, product["name"], product))

        # Prefer products matching every useful word; fall back to a majority so a near
        # miss still returns something rather than nothing.
        best = max((score for score, _, _ in scored), default=0)
        threshold = len(useful) if best >= len(useful) else max(1, (len(useful) + 1) // 2)
        scored = [entry for entry in scored if entry[0] >= threshold]
        scored.sort(key=lambda entry: (-entry[0], entry[1]))
        products = [product for _, _, product in scored]

    return products[: int(limit)] if limit else products


def get_product(product_id: str) -> dict[str, Any] | None:
    """One product with its full size/stock breakdown, or None if the slug is unknown.

    A dictionary lookup against the cached catalogue rather than two queries.
    """
    _all_products()  # ensures the cache (and its index) is warm
    return _cache_by_id.get(product_id)


def list_garment_types() -> list[str]:
    """Distinct garment types, for the browse filter chips."""
    return sorted({product["garment_type"] for product in _all_products()})


# --------------------------------------------------------------------------- users


def _row_to_user(row: sqlite3.Row) -> dict[str, Any]:
    """Public view of an account. `password_hash` is deliberately not included."""
    return {
        "id": int(row["id"]),
        "name": row["name"],
        "email": row["email"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "created_at": row["created_at"],
    }


def find_user_by_email(email: str) -> sqlite3.Row | None:
    """Look up an account case-insensitively; returns the raw row, hash included."""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,)
        ).fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> sqlite3.Row | None:
    """Look up an account by id, for stamping chat messages and greeting by name."""
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()


def email_taken(email: str) -> bool:
    return find_user_by_email(email) is not None


def create_user(
    first_name: str, last_name: str, email: str, password_hash: str
) -> dict[str, Any]:
    """Insert a new account and return its public view.

    `name` is populated alongside `first_name`/`last_name` so rows created here read the
    same way as the seeded rows, which predate the split-name columns.
    """
    full_name = f"{first_name} {last_name}".strip()
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) "
            "VALUES (?, ?, ?, ?, ?)",
            (full_name, email, password_hash, first_name, last_name),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return _row_to_user(row)
    finally:
        conn.close()


def public_user(row: sqlite3.Row) -> dict[str, Any]:
    return _row_to_user(row)


# -------------------------------------------------------------------- chat history

# How many past turns to reload. Enough for a conversation to feel continuous without
# sending an unbounded transcript to the model on every message.
CHAT_HISTORY_LIMIT = 40


def save_chat_message(
    user_id: int,
    role: str,
    content: str,
    products: list[dict[str, Any]] | None = None,
) -> int:
    """Append one turn to `chat_messages` and return its id.

    `products_json` stores the product cards that went with an assistant reply, matching
    the shape the seeded rows already use, so a reloaded reply shows its cards again
    rather than losing them.
    """
    payload = json.dumps(products) if products else None
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) "
            "VALUES (?, ?, ?, ?)",
            (int(user_id), role, content, payload),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def get_chat_history(
    user_id: int, limit: int = CHAT_HISTORY_LIMIT
) -> list[dict[str, Any]]:
    """The most recent turns for one shopper, oldest first.

    Ordered by `id`, which is the reliable insertion order - `created_at` is only
    second-resolution, so two messages in the same second could come back reversed.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, role, content, products_json, created_at FROM chat_messages "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (int(user_id), int(limit)),
        ).fetchall()
    finally:
        conn.close()

    history: list[dict[str, Any]] = []
    for row in reversed(rows):  # newest-first query, oldest-first result
        products: list[dict[str, Any]] = []
        if row["products_json"]:
            try:
                parsed = json.loads(row["products_json"])
                products = parsed if isinstance(parsed, list) else []
            except ValueError:
                products = []
        history.append(
            {
                "id": int(row["id"]),
                "role": row["role"],
                "content": row["content"],
                "products": products,
                "created_at": row["created_at"],
            }
        )
    return history


def catalogue_stats() -> dict[str, Any]:
    """Small summary used by the home page and the health check."""
    products = _all_products()
    prices = [product["price"] for product in products]
    return {
        "products": len(products),
        "min_price": min(prices) if prices else 0.0,
        "max_price": max(prices) if prices else 0.0,
        "units_in_stock": sum(product["total_stock"] for product in products),
    }
