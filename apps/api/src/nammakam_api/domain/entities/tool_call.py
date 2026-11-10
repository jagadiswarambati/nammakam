"""Tool Call Domain Entity.

Represents a mock banking tool invocation record (e.g. fund transfer, balance inquiry).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    """Record of an external tool invocation attempted by the bank agent."""

    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    is_authorized: bool = True
    error: str | None = None
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tool_call_id or not self.tool_call_id.strip():
            raise ValueError("tool_call_id cannot be empty")
        if not self.tool_name or not self.tool_name.strip():
            raise ValueError("tool_name cannot be empty")
