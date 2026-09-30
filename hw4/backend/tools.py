"""Tools the Campus Customs agent can call, plus the model wiring.

Every fact the agent states about a product has to come through one of these functions.
They are thin wrappers over `db.py`, which reads the SQLite catalogue — so a price or a
stock number in a reply is a value that was read from the database during that request,
not something the model remembered.

The model is reached through the Portkey gateway using an OpenAI-compatible client.
`PORTKEY_API_KEY` is read from the repository root `.env` and is never logged or returned.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from portkey_ai import PORTKEY_GATEWAY_URL
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

import db
from models import (
    AlternativeSuggestions,
    PriceQuote,
    ProductDescription,
    SearchResults,
    SizeAvailability,
    SizeStock,
    StockReport,
    ToolProduct,
)

# --------------------------------------------------------------------------- model setup

BACKEND_DIR = Path(__file__).resolve().parent
HW_DIR = BACKEND_DIR.parent
REPO_ROOT = HW_DIR.parent

# The key lives in the repository root .env, one level above HW 4.
load_dotenv(REPO_ROOT / ".env")
load_dotenv(HW_DIR / ".env")  # allow a local override without touching the shared file

PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")

# Everyday shop questions go to the fast model. Harder reasoning steps can point at a
# bigger one by setting CAMPUS_CUSTOMS_MODEL.
DEFAULT_MODEL = os.getenv("CAMPUS_CUSTOMS_MODEL", "gpt-5.6-luna")

MAX_PRODUCTS_PER_REPLY = 5
SEARCH_RESULT_LIMIT = 12


def build_model(model_name: str | None = None) -> OpenAIChatModel:
    """Return a PydanticAI model that talks to OpenAI through Portkey."""
    if not PORTKEY_API_KEY:
        raise RuntimeError(
            "PORTKEY_API_KEY is not set. Add it to the repository root .env file."
        )
    provider = OpenAIProvider(api_key=PORTKEY_API_KEY, base_url=PORTKEY_GATEWAY_URL)
    return OpenAIChatModel(model_name or DEFAULT_MODEL, provider=provider)


# ------------------------------------------------------------------------------- tools


LOW_STOCK_THRESHOLD = 3


def format_price(price: float) -> str:
    """One place that turns a price into shopper-facing text.

    Tools hand the model this pre-formatted string so it repeats `$68.00` rather than
    reformatting the float itself and drifting into `$68` or `68 dollars`.
    """
    return f"${price:.2f}"


def _size_note(quantity: int) -> str:
    """Plain-language reading of one stock number."""
    if quantity == 0:
        return "sold out"
    if quantity <= LOW_STOCK_THRESHOLD:
        return f"only {quantity} left"
    return f"{quantity} in stock"


def _sold_out_sizes(row: dict) -> list[str]:
    return [item["size"] for item in row["inventory"] if item["quantity"] == 0]


def _to_tool_product(row: dict) -> ToolProduct:
    """Trim a full product down to what the model needs to answer."""
    return ToolProduct(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=row["colors"],
        price=row["price"],
        price_display=format_price(row["price"]),
        sizes_in_stock=row["sizes_in_stock"],
        sold_out_sizes=_sold_out_sizes(row),
        total_stock=row["total_stock"],
    )


def search_catalogue(query: str, garment_type: str | None = None) -> SearchResults:
    """Find products matching a shopper's words.

    `query` is matched against product names, descriptions, colours and search tags, so
    shopper vocabulary ("Yale hoodie", "The Game", "navy", "Branford") works as well as
    exact product names.

    The full match count is returned alongside a capped page of results, so the agent can
    tell the difference between "these are all of them" and "these are the first few".
    """
    rows = db.list_products(search=query or None, garment_type=garment_type)
    page = rows[:SEARCH_RESULT_LIMIT]
    return SearchResults(
        query=query,
        total_matches=len(rows),
        returned=len(page),
        truncated=len(rows) > len(page),
        products=[_to_tool_product(row) for row in page],
    )


def get_product(product_id: str) -> ToolProduct | None:
    """Full details for one product, including which sizes are sold out."""
    row = db.get_product(product_id)
    return _to_tool_product(row) if row else None


def get_description(product_id: str) -> ProductDescription | None:
    """What one product is: its catalogue description and the colours it comes in."""
    row = db.get_product(product_id)
    if row is None:
        return None
    return ProductDescription(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=row["colors"],
    )


def get_price(product_id: str) -> PriceQuote | None:
    """What one product costs, read from `catalogue.price`."""
    row = db.get_product(product_id)
    if row is None:
        return None
    return PriceQuote(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        price=row["price"],
        price_display=format_price(row["price"]),
    )


def get_stock(product_id: str) -> StockReport | None:
    """Stock for every size of one product, read from the `inventory` table."""
    row = db.get_product(product_id)
    if row is None:
        return None

    sizes = [
        SizeStock(
            size=item["size"],
            quantity=int(item["quantity"]),
            in_stock=int(item["quantity"]) > 0,
            note=_size_note(int(item["quantity"])),
        )
        for item in row["inventory"]
    ]
    in_stock = row["sizes_in_stock"]
    sold_out = _sold_out_sizes(row)

    if not in_stock:
        note = f"{row['name']} is sold out in every size right now."
    elif not sold_out:
        note = f"{row['name']} is in stock in all sizes: {', '.join(in_stock)}."
    else:
        note = (
            f"{row['name']} is in stock in {', '.join(in_stock)}; "
            f"sold out in {', '.join(sold_out)}."
        )

    return StockReport(
        product_id=row["product_id"],
        name=row["name"],
        price_display=format_price(row["price"]),
        sizes=sizes,
        sizes_in_stock=in_stock,
        sold_out_sizes=sold_out,
        total_stock=row["total_stock"],
        availability_note=note,
    )


def check_size(product_id: str, size: str) -> SizeAvailability | None:
    """Whether one specific size of one product is in stock right now."""
    row = db.get_product(product_id)
    if row is None:
        return None

    wanted = size.strip().upper()
    match = next(
        (item for item in row["inventory"] if item["size"].upper() == wanted), None
    )
    quantity = int(match["quantity"]) if match else 0
    others = [s for s in row["sizes_in_stock"] if s.upper() != wanted]

    if match is None:
        note = (
            f"{wanted} is not a size we stock for {row['name']}. "
            f"We carry {', '.join(row['sizes_in_stock']) or 'no sizes right now'}."
        )
    elif quantity == 0:
        note = (
            f"{row['name']} is sold out in {wanted}. "
            + (f"We do have it in {', '.join(others)}." if others else
               "It is sold out in every other size too.")
        )
    elif quantity <= LOW_STOCK_THRESHOLD:
        note = f"Only {quantity} left of {row['name']} in {wanted}."
    else:
        note = f"{row['name']} is in stock in {wanted} - {quantity} on hand."

    return SizeAvailability(
        product_id=row["product_id"],
        name=row["name"],
        size=wanted,
        quantity=quantity,
        in_stock=quantity > 0,
        price=row["price"],
        price_display=format_price(row["price"]),
        other_sizes_in_stock=others,
        availability_note=note,
    )


# `catalogue.garment_type` has 22 near-duplicate spellings, so "same kind of thing" needs
# a normalised family. Order matters: "full-zip hooded sweatshirt" is a hoodie, not a zip.
_FAMILY_RULES: list[tuple[tuple[str, ...], str]] = [
    (("hood",), "hoodie"),
    (("quarter-zip", "1/4", "quarter zip"), "quarter-zip"),
    (("crew",), "crewneck"),
    (("jacket", "bomber"), "jacket"),
    (("t-shirt", "t shirt", "tee"), "t-shirt"),
    (("performance", "long-sleeve", "dry zone"), "performance shirt"),
    (("mockneck", "sweater", "fleece"), "sweatshirt"),
]

MAX_ALTERNATIVES = 3


def garment_family(garment_type: str) -> str:
    """Group the 22 garment_type spellings into a handful of shopper-meaningful families."""
    text = garment_type.lower()
    for needles, family in _FAMILY_RULES:
        if any(needle in text for needle in needles):
            return family
    return text


def suggest_alternatives(
    product_id: str, size: str | None = None
) -> AlternativeSuggestions | None:
    """Find genuine substitutes for a product the shopper cannot have.

    Used when the size or colour they asked for is unavailable. Candidates are the same
    family of garment, actually in stock (in the requested size when one was named), and
    ranked by how close the price is to what they were already looking at - so the
    suggestion reads as a fair swap rather than an upsell.
    """
    base = db.get_product(product_id)
    if base is None:
        return None

    wanted = size.strip().upper() if size else None
    family = garment_family(base["garment_type"])

    def has_size(row: dict) -> bool:
        if wanted is None:
            return row["total_stock"] > 0
        return any(
            item["size"].upper() == wanted and item["quantity"] > 0
            for item in row["inventory"]
        )

    everything = [
        row for row in db.list_products() if row["product_id"] != base["product_id"]
    ]

    same_family = [
        row
        for row in everything
        if garment_family(row["garment_type"]) == family and has_size(row)
    ]
    if same_family:
        candidates, basis = same_family, (
            f"same kind of garment ({family}), in stock"
            + (f" in {wanted}" if wanted else "")
        )
    else:
        # Nothing in the same family fits. A different garment in their size still beats
        # a dead end, but say what it is rather than implying it is the same thing.
        other = [row for row in everything if has_size(row)]
        if not other:
            return AlternativeSuggestions(
                for_product_id=base["product_id"],
                for_product_name=base["name"],
                size=wanted,
                basis="nothing comparable is in stock",
                products=[],
            )
        candidates, basis = other, (
            "a different kind of garment, in stock" + (f" in {wanted}" if wanted else "")
        )

    candidates.sort(key=lambda row: (abs(row["price"] - base["price"]), row["name"]))
    return AlternativeSuggestions(
        for_product_id=base["product_id"],
        for_product_name=base["name"],
        size=wanted,
        basis=basis,
        products=[_to_tool_product(row) for row in candidates[:MAX_ALTERNATIVES]],
    )


def list_garment_types() -> list[str]:
    """Every garment category we carry, for "what kinds of things do you sell?"."""
    return db.list_garment_types()


def hydrate_products(product_ids: list[str]) -> list[dict]:
    """Re-read the agent's chosen product ids from the database.

    This is the step that keeps the cards honest: the agent only ever hands back ids, and
    the real name, price, image and stock are read fresh here. Unknown ids are dropped
    rather than faked, and duplicates are collapsed.
    """
    products: list[dict] = []
    seen: set[str] = set()
    for product_id in product_ids:
        if product_id in seen:
            continue
        seen.add(product_id)
        row = db.get_product(product_id)
        if row is not None:
            products.append(row)
        if len(products) >= MAX_PRODUCTS_PER_REPLY:
            break
    return products
