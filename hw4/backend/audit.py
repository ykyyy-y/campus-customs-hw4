"""Append-only audit trail for the agent loop.

Every shopper turn writes three kinds of record to `output/audit_trail.json`:

* `run_start` — who asked, where they were, what they asked
* `tool_call`  — one per tool the agent called, with short args and a short result
* `run_end`    — the stop reason, counts and timings

**The file is never wiped.** Records are only ever appended, across restarts and across
runs. Writes go through a lock and land via `os.replace()` on a temporary file, so a crash
mid-write leaves the previous trail intact rather than a half-written file.

The stored file is a single JSON array so it can be opened and read directly. Appending
means read-modify-write, which is correct for one Uvicorn process; a multi-process
deployment would want JSON Lines instead, and `SUMMARY_LIMIT` keeps each record small
enough that re-serialising stays cheap.

Nothing sensitive is written: no passwords (the agent never sees one), no email addresses,
and message text is truncated. Shoppers are identified by `user_id` only.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parent
AUDIT_PATH = BACKEND_DIR.parent / "output" / "audit_trail.json"

# How much of any single string we keep. Enough to understand what happened, short enough
# that the trail stays readable and the file does not balloon.
SUMMARY_LIMIT = 160

_lock = threading.Lock()


def new_run_id() -> str:
    """Short id tying one turn's records together."""
    return uuid.uuid4().hex[:12]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def summarise(value: Any, limit: int = SUMMARY_LIMIT) -> Any:
    """Shorten a value for the trail without losing what it was.

    Long strings are truncated, lists are counted and sampled, and Pydantic models are
    reduced to the fields that matter for an audit rather than dumped whole.
    """
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        text = " ".join(value.split())
        return text if len(text) <= limit else text[:limit] + "..."
    if isinstance(value, dict):
        return {key: summarise(item, 60) for key, item in list(value.items())[:8]}
    if isinstance(value, (list, tuple)):
        if not value:
            return []
        return {"count": len(value), "first": summarise(value[0], 80)}
    # Pydantic models and dataclass-like objects
    for attr in ("model_dump",):
        if hasattr(value, attr):
            try:
                return summarise(getattr(value, attr)(), limit)
            except Exception:  # pragma: no cover - never let auditing break a reply
                break
    return summarise(str(value), limit)


def _append(record: dict[str, Any]) -> None:
    """Append one record to the trail. Failures are swallowed on purpose.

    Auditing must never take the shop down: if the trail cannot be written, the shopper
    still gets their answer.
    """
    try:
        with _lock:
            AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

            entries: list[dict[str, Any]] = []
            if AUDIT_PATH.exists():
                try:
                    loaded = json.loads(AUDIT_PATH.read_text(encoding="utf-8") or "[]")
                    if isinstance(loaded, list):
                        entries = loaded
                except ValueError:
                    # A corrupt trail is preserved rather than discarded, so the history
                    # is never silently lost.
                    AUDIT_PATH.replace(AUDIT_PATH.with_suffix(".corrupt.json"))
                    entries = []

            entries.append(record)

            temp = AUDIT_PATH.with_suffix(".tmp")
            temp.write_text(json.dumps(entries, indent=2), encoding="utf-8")
            os.replace(temp, AUDIT_PATH)  # atomic: never a half-written trail
    except Exception:  # pragma: no cover
        pass


def log_run_start(
    run_id: str,
    message: str,
    user_id: int | None,
    page: str | None,
    product_id: str | None,
    model: str,
) -> None:
    _append(
        {
            "ts": _now(),
            "run_id": run_id,
            "event": "run_start",
            "model": model,
            "user_id": user_id,
            "signed_in": user_id is not None,
            "page": page,
            "page_product_id": product_id,
            "message": summarise(message),
        }
    )


def log_tool_call(
    run_id: str, tool: str, args: dict[str, Any], result: Any, ms: float | None = None
) -> None:
    _append(
        {
            "ts": _now(),
            "run_id": run_id,
            "event": "tool_call",
            "tool": tool,
            "args": summarise(args),
            "result": summarise(result),
            "duration_ms": round(ms, 1) if ms is not None else None,
        }
    )


def log_run_end(
    run_id: str,
    stop_reason: str,
    reply: str | None = None,
    product_ids: list[str] | None = None,
    tool_calls: int | None = None,
    requests: int | None = None,
    ms: float | None = None,
    detail: str | None = None,
) -> None:
    """Close out a run.

    `stop_reason` is one of:
      ok              the agent answered normally
      empty_message   rejected before the model was called
      usage_limit     hit the request or tool-call ceiling
      model_error     the provider refused or failed (includes content filtering)
      agent_error     anything else raised inside the agent loop
    """
    _append(
        {
            "ts": _now(),
            "run_id": run_id,
            "event": "run_end",
            "stop_reason": stop_reason,
            "reply": summarise(reply) if reply else None,
            "product_ids": product_ids or [],
            "tool_calls": tool_calls,
            "model_requests": requests,
            "duration_ms": round(ms, 1) if ms is not None else None,
            "detail": summarise(detail, 120) if detail else None,
        }
    )


def stats() -> dict[str, Any]:
    """Small summary for /api/health, so the trail is visible without opening the file."""
    if not AUDIT_PATH.exists():
        return {"entries": 0, "runs": 0, "path": AUDIT_PATH.name}
    try:
        entries = json.loads(AUDIT_PATH.read_text(encoding="utf-8") or "[]")
    except ValueError:
        return {"entries": 0, "runs": 0, "path": AUDIT_PATH.name, "error": "unreadable"}
    return {
        "entries": len(entries),
        "runs": sum(1 for e in entries if e.get("event") == "run_start"),
        "tool_calls": sum(1 for e in entries if e.get("event") == "tool_call"),
        "path": AUDIT_PATH.name,
        "first_ts": entries[0].get("ts") if entries else None,
        "last_ts": entries[-1].get("ts") if entries else None,
    }
