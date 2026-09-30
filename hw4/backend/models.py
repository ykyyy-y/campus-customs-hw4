"""Pydantic types shared by the FastAPI app and the PydanticAI agent.

The `Product` shape is deliberately identical to the objects already stored in
`chat_messages.products_json`, so a reply loaded from history renders the same cards as a
live one.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, EmailStr, Field

# --------------------------------------------------------------------------- catalogue


class InventoryItem(BaseModel):
    """Stock for one size of one product."""

    size: str = Field(description="XS, S, M, L, XL or XXL")
    quantity: int = Field(description="Units on hand; 0 means that size is sold out")


class Product(BaseModel):
    """A catalogue product joined to its per-size stock."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str] = []
    search_tags: list[str] = []
    image_file_path: str
    image_url: str = Field(description="Served path, e.g. /media/products/foo.jpg")
    price: float
    inventory: list[InventoryItem] = []
    total_stock: int = 0
    sizes_in_stock: list[str] = []


class CatalogueStats(BaseModel):
    """Headline numbers for the home page."""

    products: int
    min_price: float
    max_price: float
    units_in_stock: int


# --------------------------------------------------------------------------- accounts


class SignupRequest(BaseModel):
    """Everything the create-account form collects. Plaintext lives only in transit."""

    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class PublicUser(BaseModel):
    """What the API is willing to say about an account. No password field exists here."""

    id: int
    name: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    created_at: str | None = None


class AuthResponse(BaseModel):
    """Answer to a successful sign-up or sign-in.

    `session_token` is the only thing that proves who a later request is from. The browser
    stores it and sends it back as `Authorization: Bearer <token>`.
    """

    user: PublicUser
    message: str
    session_token: str


# ------------------------------------------------------------------------------- chat


class PageContext(BaseModel):
    """Where the shopper is on the site when they send a message.

    This is what lets "do you have this in pink?" work: if the shopper is on a product
    page, the agent is told which product "this" refers to.
    """

    page: str | None = Field(
        default=None, description="'home', 'products', 'product', 'about', 'auth'"
    )
    path: str | None = Field(default=None, description="The browser path, for context")
    product_id: str | None = Field(
        default=None, description="Set when the shopper is on a single product page"
    )
    search: str | None = Field(
        default=None, description="What they have typed in the catalogue search box"
    )
    garment_type: str | None = Field(
        default=None, description="Catalogue filter they have applied"
    )


class ChatRequest(BaseModel):
    """A shopper turn from the website.

    There is deliberately **no `user_id`** here. Identity comes only from the session
    token in the Authorization header, so a browser cannot read or write another
    shopper's conversation by changing a number in the request body.
    """

    message: str = Field(min_length=1, max_length=2000)
    page_context: PageContext | None = None


class ChatResponse(BaseModel):
    """An assistant turn: the words, plus the cards the page should show."""

    reply: str
    products: list[Product] = []
    saved: bool = Field(
        default=False, description="True when this turn was written to chat_messages"
    )


class ChatHistoryMessage(BaseModel):
    """One stored turn, replayed into the widget when a shopper returns."""

    id: int
    role: str
    content: str
    products: list[Product] = []
    created_at: str | None = None


class ChatHistoryResponse(BaseModel):
    user_id: int
    messages: list[ChatHistoryMessage] = []


# ------------------------------------------------------------------------- agent types


class AgentReply(BaseModel):
    """The agent's structured output.

    The agent returns product *ids* rather than whole products: it should never be in a
    position to retype a price or a stock number, so `agent.py` re-reads every id from the
    database and builds the real `Product` objects for the cards.
    """

    reply: str = Field(description="What to say to the shopper. Short, warm, plain.")
    product_ids: list[str] = Field(
        default_factory=list,
        description=(
            "product_id values for items mentioned in the reply, in the order they should "
            "appear as cards. Empty when the answer names no specific product. At most 5."
        ),
    )


@dataclass
class ChatDeps:
    """Per-request context handed to the agent and its tools.

    Two kinds of context travel together here:

    * **Who is chatting** - resolved from the database by `user_id`, never taken from the
      request body, so a browser cannot claim to be someone else by editing a name field.
    * **Where they are** - the page they are on, so "this" and "it" resolve to a real
      product.

    Both are `None` for a guest, and the agent is told so explicitly.
    """

    run_id: str | None = None

    # who
    user_id: int | None = None
    first_name: str | None = None
    full_name: str | None = None
    email: str | None = None
    is_logged_in: bool = False

    # where
    page: str | None = None
    path: str | None = None
    current_product_id: str | None = None
    current_product_name: str | None = None
    search: str | None = None
    garment_type: str | None = None


class ToolProduct(BaseModel):
    """Trimmed product view returned by catalogue search.

    Deliberately narrower than `Product`: the model does not need image paths or search
    tags to answer, and a smaller payload keeps more of the catalogue inside the context
    window when a search matches many rows.
    """

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str] = []
    price: float
    price_display: str = Field(description="Pre-formatted, e.g. '$68.00' - quote verbatim")
    sizes_in_stock: list[str] = []
    sold_out_sizes: list[str] = []
    total_stock: int = 0


class SearchResults(BaseModel):
    """A page of catalogue matches, plus how many there really were.

    Search returns at most a dozen rows to keep the context small. Without a total the
    model cannot tell a complete result set from a truncated one, and will happily report
    "we have two crewnecks under $60" when the catalogue holds twenty-eight. `truncated`
    and `total_matches` exist so it can be honest about that.
    """

    query: str
    total_matches: int = Field(description="How many products matched in total")
    returned: int = Field(description="How many are in this list")
    truncated: bool = Field(
        description="True when there are more matches than are shown here. Do not state a "
        "count or say 'we have only these' when this is True - say there are more."
    )
    products: list[ToolProduct] = []


class AlternativeSuggestions(BaseModel):
    """Real substitutes for something the shopper cannot have.

    Every entry is a row that is actually in stock, so offering one is never a guess.
    """

    for_product_id: str
    for_product_name: str
    size: str | None = Field(default=None, description="The size the shopper wanted")
    basis: str = Field(
        description="How these were chosen, e.g. 'same garment type, in stock in XL'"
    )
    products: list[ToolProduct] = Field(
        default_factory=list,
        description="Closest in price first. Empty means offer nothing rather than a stretch.",
    )


class ProductDescription(BaseModel):
    """What a product *is*: the answer to "tell me about this one"."""

    product_id: str
    name: str
    garment_type: str
    description: str = Field(description="The catalogue description, verbatim")
    colors: list[str] = Field(
        default_factory=list,
        description="Every colour this product actually comes in. If a colour is not in "
        "this list, we do not have it in that colour.",
    )


class PriceQuote(BaseModel):
    """What a product costs. One price per product; there are no per-size prices."""

    product_id: str
    name: str
    garment_type: str
    price: float
    price_display: str = Field(
        description="The price formatted for the shopper, e.g. '$68.00'. Say this string "
        "exactly as given rather than reformatting the number."
    )


class SizeStock(BaseModel):
    """Stock for one size, with the plain-language reading already done."""

    size: str
    quantity: int
    in_stock: bool
    note: str = Field(description="e.g. '15 in stock', 'only 2 left', 'sold out'")


class StockReport(BaseModel):
    """Stock across every size of one product."""

    product_id: str
    name: str
    price_display: str
    sizes: list[SizeStock] = Field(
        default_factory=list, description="All six sizes, XS through XXL, in that order"
    )
    sizes_in_stock: list[str] = []
    sold_out_sizes: list[str] = Field(
        default_factory=list,
        description="Sizes at zero. Tell the shopper plainly if their size is here.",
    )
    total_stock: int = 0
    availability_note: str = Field(
        description="One honest sentence summarising availability. Safe to repeat as-is."
    )


class SizeAvailability(BaseModel):
    """The answer to "do you have it in L?" for one specific size."""

    product_id: str
    name: str
    size: str
    quantity: int
    in_stock: bool = Field(description="False means sold out in this size. Say so clearly.")
    price: float
    price_display: str
    other_sizes_in_stock: list[str] = Field(
        default_factory=list,
        description="Sizes we do have, to offer when the requested size is sold out",
    )
    availability_note: str = Field(
        description="One honest sentence about this size. Safe to repeat as-is."
    )
