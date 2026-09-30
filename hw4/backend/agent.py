"""The Campus Customs shop agent.

A PydanticAI `Agent` whose system prompt is the text of `prompts/prompt.md`, whose tools
come from `tools.py`, and whose structured output is `AgentReply` (words plus product ids).

The prompt file is the single place the shop's voice and safety rules live; editing that
file changes the agent's behaviour with no code change.

Run a question straight from the command line:

    python agent.py "what hoodies do you have?"
"""

from __future__ import annotations

import asyncio
import sys
import time
from functools import lru_cache
from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.usage import UsageLimits

import audit
import tools
from models import (
    AgentReply,
    AlternativeSuggestions,
    ChatDeps,
    PriceQuote,
    Product,
    ProductDescription,
    SearchResults,
    SizeAvailability,
    StockReport,
    ToolProduct,
)

BACKEND_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"

# A healthy turn is two model requests: decide to look something up, then answer with the
# result. The ceilings sit above that but low enough that a runaway tool loop is stopped
# rather than left to burn budget.
USAGE_LIMITS = UsageLimits(request_limit=6, tool_calls_limit=6)


def _audited(ctx: RunContext[ChatDeps], tool: str, args: dict, call):
    """Run a tool, record it on the audit trail, and hand the result back.

    Every tool goes through here so the trail cannot drift out of step with what the
    agent actually did. Timing is measured around the call, and a raising tool is logged
    as an error rather than vanishing from the record.
    """
    started = time.perf_counter()
    try:
        result = call()
    except Exception as exc:
        audit.log_tool_call(
            ctx.deps.run_id or "unknown",
            tool,
            args,
            f"ERROR: {type(exc).__name__}: {exc}",
            (time.perf_counter() - started) * 1000,
        )
        raise
    audit.log_tool_call(
        ctx.deps.run_id or "unknown",
        tool,
        args,
        result,
        (time.perf_counter() - started) * 1000,
    )
    return result


def load_prompt() -> str:
    """Read the system prompt from disk."""
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"System prompt not found at {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


@lru_cache(maxsize=1)
def get_agent() -> Agent[ChatDeps, AgentReply]:
    """Build the agent once and reuse it across requests.

    Cached because the prompt file and the model client do not change between turns, and
    rebuilding the agent per request would re-read the file and re-create the HTTP client
    on every message.
    """
    agent = Agent(
        tools.build_model(),
        deps_type=ChatDeps,
        output_type=AgentReply,
        instructions=load_prompt(),
        retries=2,
    )

    @agent.instructions
    def who_is_chatting(ctx: RunContext[ChatDeps]) -> str:
        """Who the shopper is. Resolved from the database, never from the request body."""
        deps = ctx.deps
        if not deps.is_logged_in:
            return (
                "SHOPPER: a guest, not signed in. You do not know their name. Do not "
                "guess it, do not ask them to log in, and do not refer to anything from "
                "an earlier visit - this conversation starts fresh."
            )
        lines = ["SHOPPER: signed in."]
        if deps.first_name:
            lines.append(f"- First name: {deps.first_name} (use it naturally, not every turn)")
        if deps.full_name:
            lines.append(f"- Full name: {deps.full_name}")
        if deps.email:
            lines.append(f"- Email on file: {deps.email} (do not read it back unless asked)")
        lines.append(
            "Earlier messages in this conversation are their real history with the shop, "
            "so you may refer back to what they were looking at."
        )
        return "\n".join(lines)

    @agent.instructions
    def where_they_are(ctx: RunContext[ChatDeps]) -> str:
        """The page the shopper is on, so "this" and "it" resolve to a real product."""
        deps = ctx.deps
        if deps.current_product_id:
            return (
                "PAGE: the shopper is looking at a single product page for "
                f'"{deps.current_product_name}" (product_id: {deps.current_product_id}).\n'
                'When they say "this", "it", "this one" or "this hoodie" with no other '
                "product named, they mean that product. Call the lookup tools with that "
                "product_id rather than searching again or asking which item they mean."
            )
        if deps.page == "products":
            filters = []
            if deps.search:
                filters.append(f'search box: "{deps.search}"')
            if deps.garment_type:
                filters.append(f'garment filter: "{deps.garment_type}"')
            suffix = f" They have {', '.join(filters)}." if filters else ""
            return (
                "PAGE: the shopper is browsing the full catalogue listing." + suffix
            )
        if deps.page == "home":
            return "PAGE: the shopper is on the home page and has not opened an item yet."
        if deps.page == "about":
            return "PAGE: the shopper is reading the About Us page."
        return (
            "PAGE: not known. If the shopper says \"this\" without naming a product, ask "
            "which item they mean."
        )

    # --- tools ------------------------------------------------------------------

    @agent.tool
    def search_catalogue(
        ctx: RunContext[ChatDeps], query: str, garment_type: str | None = None
    ) -> SearchResults:
        """Search the Campus Customs catalogue.

        Use this first for any question about what we sell. Matches product names,
        descriptions, colours and search tags, so shopper words like "Yale hoodie",
        "The Game", "navy" or a residential college name all work.

        Check `total_matches` and `truncated` before stating how many we have: the
        `products` list is capped, so it is often only the first few of many.

        Args:
            query: What the shopper is looking for, in their own words.
            garment_type: Optional category filter, e.g. "hoodie" or "crewneck".
        """
        return _audited(ctx, "search_catalogue",
                        {"query": query, "garment_type": garment_type},
                        lambda: tools.search_catalogue(query, garment_type))

    @agent.tool
    def get_product_details(ctx: RunContext[ChatDeps], product_id: str) -> ToolProduct | None:
        """Full details for one product: description, colours, price, and which sizes are
        in stock or sold out. Returns nothing if the product_id is not in the catalogue.

        Args:
            product_id: The product's catalogue id, e.g. "basic-hoodie-big-yale".
        """
        return _audited(ctx, "get_product_details", {"product_id": product_id},
                        lambda: tools.get_product(product_id))

    @agent.tool
    def get_product_description(
        ctx: RunContext[ChatDeps], product_id: str
    ) -> ProductDescription | None:
        """The catalogue description for one product, and every colour it comes in.

        Use this for "tell me about it" or "what colour is it?" questions. If a colour is
        not in the returned list, we do not carry the product in that colour - say so.

        Args:
            product_id: The product's catalogue id, e.g. "basic-hoodie-big-yale".
        """
        return _audited(ctx, "get_product_description", {"product_id": product_id},
                        lambda: tools.get_description(product_id))

    @agent.tool
    def get_product_price(ctx: RunContext[ChatDeps], product_id: str) -> PriceQuote | None:
        """What one product costs, read from the catalogue.

        Always call this before stating a price. Repeat `price_display` exactly as given.
        There is one price per product; sizes do not change the price.

        Args:
            product_id: The product's catalogue id.
        """
        return _audited(ctx, "get_product_price", {"product_id": product_id},
                        lambda: tools.get_price(product_id))

    @agent.tool
    def get_stock_by_size(ctx: RunContext[ChatDeps], product_id: str) -> StockReport | None:
        """Stock for every size of one product, XS through XXL.

        Use this when the shopper asks what sizes are available, or has not named a size
        yet. `sold_out_sizes` must be reported plainly rather than left out.

        Args:
            product_id: The product's catalogue id.
        """
        return _audited(ctx, "get_stock_by_size", {"product_id": product_id},
                        lambda: tools.get_stock(product_id))

    @agent.tool
    def check_size_stock(
        ctx: RunContext[ChatDeps], product_id: str, size: str
    ) -> SizeAvailability | None:
        """Check whether one specific size of one product is in stock right now.

        Always use this before telling a shopper a size is available. Returns the exact
        quantity on hand and the other sizes we do have.

        Args:
            product_id: The product's catalogue id.
            size: One of XS, S, M, L, XL, XXL.
        """
        return _audited(ctx, "check_size_stock", {"product_id": product_id, "size": size},
                        lambda: tools.check_size(product_id, size))

    @agent.tool
    def get_product_on_screen(ctx: RunContext[ChatDeps]) -> ToolProduct | None:
        """The product the shopper is currently looking at, if they are on a product page.

        Use this when they say "this", "it" or "this one" without naming a product.
        Returns nothing if they are not on a single product page - in that case ask which
        item they mean rather than guessing.
        """
        if not ctx.deps.current_product_id:
            return None
        return _audited(ctx, "get_product_on_screen",
                        {"product_id": ctx.deps.current_product_id},
                        lambda: tools.get_product(ctx.deps.current_product_id))

    @agent.tool
    def suggest_alternatives(
        ctx: RunContext[ChatDeps], product_id: str, size: str | None = None
    ) -> AlternativeSuggestions | None:
        """Find real substitutes when a shopper cannot have what they asked for.

        Call this whenever a size or colour is unavailable, so you can offer a genuine
        second option instead of leaving them at a dead end. Everything returned is
        actually in stock; `basis` says how they were chosen, and an empty list means
        offer nothing rather than a stretch.

        Args:
            product_id: The product they wanted.
            size: The size they wanted, if they named one.
        """
        return _audited(ctx, "suggest_alternatives", {"product_id": product_id, "size": size},
                        lambda: tools.suggest_alternatives(product_id, size))

    @agent.tool
    def list_garment_types(ctx: RunContext[ChatDeps]) -> list[str]:
        """Every garment category we carry. Use for broad questions like "what do you
        sell?" before naming specific items."""
        return _audited(ctx, "list_garment_types", {},
                        lambda: tools.list_garment_types())

    return agent


def build_message_history(stored: list[dict]) -> list[ModelMessage]:
    """Turn rows from `chat_messages` into PydanticAI conversation history.

    Only the text of each turn is replayed, not the tool calls that produced it. That is
    deliberate: a price or a stock number from last week must not be reused as if it were
    current, so the agent has to look facts up again while still remembering what the
    shopper was talking about.
    """
    history: list[ModelMessage] = []
    for row in stored:
        content = (row.get("content") or "").strip()
        if not content:
            continue
        if row.get("role") == "user":
            history.append(ModelRequest(parts=[UserPromptPart(content=content)]))
        elif row.get("role") == "assistant":
            history.append(ModelResponse(parts=[TextPart(content=content)]))
    return history


async def answer(
    message: str,
    deps: ChatDeps | None = None,
    history: list[dict] | None = None,
) -> tuple[str, list[Product]]:
    """Run one shopper turn and return the words plus the real product cards.

    The agent supplies product *ids*; the products themselves are re-read from the
    database here, so a card can never show a price or a stock number the model invented.
    """
    deps = deps or ChatDeps()
    deps.run_id = deps.run_id or audit.new_run_id()

    audit.log_run_start(
        deps.run_id,
        message,
        deps.user_id,
        deps.page,
        deps.current_product_id,
        tools.DEFAULT_MODEL,
    )
    started = time.perf_counter()

    try:
        result = await get_agent().run(
            message,
            deps=deps,
            message_history=build_message_history(history) if history else None,
            usage_limits=USAGE_LIMITS,
        )
    except UsageLimitExceeded as exc:
        audit.log_run_end(
            deps.run_id, "usage_limit", ms=(time.perf_counter() - started) * 1000,
            detail=str(exc),
        )
        raise
    except ModelHTTPError as exc:
        # Includes provider-side refusals such as content filtering.
        audit.log_run_end(
            deps.run_id, "model_error", ms=(time.perf_counter() - started) * 1000,
            detail=f"{exc.status_code}: {exc}",
        )
        raise
    except Exception as exc:
        audit.log_run_end(
            deps.run_id, "agent_error", ms=(time.perf_counter() - started) * 1000,
            detail=f"{type(exc).__name__}: {exc}",
        )
        raise

    # Building the cards is inside the guard too: a failure here still ends the run in
    # the trail rather than leaving a run_start with nothing after it.
    try:
        output: AgentReply = result.output
        products = [Product(**row) for row in tools.hydrate_products(output.product_ids)]
        usage = result.usage  # a property on AgentRunResult, not a method
    except Exception as exc:
        audit.log_run_end(
            deps.run_id, "agent_error", ms=(time.perf_counter() - started) * 1000,
            detail=f"{type(exc).__name__}: {exc}",
        )
        raise

    audit.log_run_end(
        deps.run_id,
        "ok",
        reply=output.reply,
        product_ids=[product.product_id for product in products],
        tool_calls=getattr(usage, "tool_calls", None),
        requests=getattr(usage, "requests", None),
        ms=(time.perf_counter() - started) * 1000,
    )
    return output.reply, products


def main() -> None:
    question = " ".join(sys.argv[1:]) or "What hoodies do you have?"
    reply, products = asyncio.run(answer(question))
    print(f"Q: {question}\n")
    print(reply)
    if products:
        print("\nCards:")
        for product in products:
            print(f"  - {product.name} ${product.price:.2f} ({product.total_stock} in stock)")


if __name__ == "__main__":
    main()
