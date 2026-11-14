import asyncio
from pathlib import Path
from typing import Any

import pytest

from cycle_validation.agent.hooks import (
    ALLOWED_TOOLS,
    ToolPolicy,
    check_tool_call,
    make_pre_tool_use_hook,
)

FILE_A = Path(__file__).resolve()
FILE_B = FILE_A.with_name("conftest.py")
POLICY = ToolPolicy.for_files([FILE_A], FILE_A.parent, read_limit=40, grep_max_context=10)


def read(**fields: Any) -> dict[str, Any]:
    return {"file_path": str(FILE_A), **fields}


def test_allowed_tools() -> None:
    assert ALLOWED_TOOLS == ("Read", "Grep")


def test_read_window_is_allowed() -> None:
    assert check_tool_call("Read", read(offset=10, limit=30), POLICY).allowed
    assert check_tool_call("Read", read(limit=40), POLICY).allowed


@pytest.mark.parametrize("limit", [None, 41, 0, -3, True, "30", 2.5])
def test_read_without_valid_limit_is_denied(limit: object) -> None:
    fields = {} if limit is None else {"limit": limit}
    decision = check_tool_call("Read", read(**fields), POLICY)
    assert not decision.allowed
    assert "limit" in decision.reason


def test_file_not_allowed_is_denied_even_in_same_folder() -> None:
    decision = check_tool_call("Read", {"file_path": str(FILE_B), "limit": 10}, POLICY)
    assert not decision.allowed


def test_relative_path_is_resolved_against_base_dir() -> None:
    assert check_tool_call("Read", {"file_path": FILE_A.name, "limit": 10}, POLICY).allowed


def test_grep_needs_an_allowed_file_path() -> None:
    assert check_tool_call("Grep", {"pattern": "x", "path": str(FILE_A)}, POLICY).allowed
    assert not check_tool_call("Grep", {"pattern": "x"}, POLICY).allowed
    assert not check_tool_call("Grep", {"pattern": "x", "path": str(FILE_A.parent)}, POLICY).allowed


def test_grep_context_is_limited() -> None:
    ok = {"pattern": "x", "path": str(FILE_A), "-C": 10}
    too_wide = {"pattern": "x", "path": str(FILE_A), "-C": 11}
    assert check_tool_call("Grep", ok, POLICY).allowed
    assert not check_tool_call("Grep", too_wide, POLICY).allowed


@pytest.mark.parametrize("tool", ["Bash", "Write", "Glob", "WebFetch"])
def test_other_tools_are_denied(tool: str) -> None:
    assert not check_tool_call(tool, {}, POLICY).allowed


def test_hook_format() -> None:
    hook = make_pre_tool_use_hook(POLICY)
    allowed = asyncio.run(hook({"tool_name": "Read", "tool_input": read(limit=10)}, "t1", None))
    assert allowed == {}
    denied = asyncio.run(hook({"tool_name": "Bash", "tool_input": {}}, "t2", None))
    output = denied["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    assert output["permissionDecisionReason"]
