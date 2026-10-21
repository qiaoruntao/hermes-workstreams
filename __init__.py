"""Hermes entry point for the Workstreams plugin."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hermes_workstreams import tool as link_tool
from hermes_workstreams.inject import FocusInjector

logger = logging.getLogger(__name__)
_injector = FocusInjector()


def on_pre_llm_call(**kwargs: Any) -> dict | None:
    try:
        return _injector(**kwargs)
    except Exception:
        logger.exception("Workstreams failed to build focus context")
        return None


def register(ctx: Any) -> None:
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_tool(name="workstream_link", toolset="workstreams", schema=link_tool.SCHEMA,
                      handler=link_tool.handle, emoji="🎯")
    ctx.register_skill(
        "workstream-focus",
        ROOT / "skills" / "workstream-focus" / "SKILL.md",
        description="Use when a request starts or continues a multi-session workstream. Link and keep FOCUS.md.",
    )
