"""Tests for the KEEL MCP server.

These build a FastMCP server bound to a temp repo and call tools in-process via
`server.call_tool`, exercising the real MCP machinery (schema generation,
serialization, error wrapping) without needing a separate client process.

Skipped entirely if the optional `mcp` dependency isn't installed.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

mcp = pytest.importorskip("mcp", reason="optional 'mcp' extra not installed")

from keel.mcp_server import build_server, resolve_root  # noqa: E402


def call(server, name: str, args: dict):
    """Call a tool and return its structured result (the dict/list/str payload)."""
    content, structured = asyncio.run(server.call_tool(name, args))
    # FastMCP returns (content_blocks, structured_result). Prefer structured.
    if isinstance(structured, dict) and "result" in structured:
        return structured["result"]
    return structured


@pytest.fixture
def server(project_layout: Path):
    return build_server(project_layout)


# ─── tool registration ───────────────────────────────────────────────────────


def test_all_expected_tools_registered(server):
    tools = asyncio.run(server.list_tools())
    names = {t.name for t in tools}
    expected = {
        "keel_project_info",
        "keel_list_tasks",
        "keel_get_task",
        "keel_read_task_file",
        "keel_create_task",
        "keel_build_context",
        "keel_verify_task",
        "keel_read_governance",
        "keel_list_governance",
        "keel_get_spec_model",
        "keel_update_code_map",
        "keel_skills_index",
        "keel_list_skills",
        "keel_get_skill",
        "keel_search_skills",
        "keel_load_skill_file",
        "keel_create_skill",
    }
    assert expected <= names


def test_every_tool_has_a_description(server):
    tools = asyncio.run(server.list_tools())
    for t in tools:
        assert t.description and t.description.strip(), f"{t.name} lacks a description"


# ─── orientation & governance ────────────────────────────────────────────────


def test_project_info(server):
    info = call(server, "keel_project_info", {})
    assert info["project_prefix"] == "TEST"
    assert "PRINCIPLES.md" in info["governance_docs"]


def test_read_governance(server):
    text = call(server, "keel_read_governance", {"name": "PRINCIPLES.md"})
    assert "P-1" in text


# ─── tasks roundtrip ─────────────────────────────────────────────────────────


def test_task_lifecycle_via_tools(server):
    created = call(server, "keel_create_task", {"slug": "mcp-task"})
    assert created["task_id"] == "TEST-001-mcp-task"

    listed = call(server, "keel_list_tasks", {})
    assert any(t["task_id"] == "TEST-001-mcp-task" for t in listed)

    # write a brief with relevant sources, then build context
    brief = "# t\n\n## Relevant sources\n- AGENTS.md\n- PRINCIPLES.md: P-1\n"
    Path(created["brief"]).write_text(brief)
    ctx = call(server, "keel_build_context", {"task_id": "TEST-001-mcp-task"})
    assert ctx["sources"] == 2

    body = call(
        server,
        "keel_read_task_file",
        {"task_id": "TEST-001-mcp-task", "filename": "context.md"},
    )
    assert "## P-1 — be honest" in body


def test_verify_task_via_tool(server):
    created = call(server, "keel_create_task", {"slug": "verify-mcp"})
    Path(created["acceptance"]).write_text(
        "task: TEST-001-verify-mcp\n"
        "checks:\n  - name: ok\n    run: 'true'\n"
        "scope_allowlist: []\n"
    )
    result = call(server, "keel_verify_task", {"task_id": "TEST-001-verify-mcp"})
    assert result["passed"] is True
    assert any(c["name"] == "ok" for c in result["checks"])


# ─── skills ──────────────────────────────────────────────────────────────────


def test_skills_index_and_load(server):
    index = call(server, "keel_skills_index", {})
    assert "dev-plan-task" in index

    skill = call(server, "keel_get_skill", {"skill_id": "dev-plan-task"})
    assert "body" in skill and skill["body"]

    f = call(
        server,
        "keel_load_skill_file",
        {"skill_id": "example-csv-clean", "relpath": "references/rules.md"},
    )
    assert "cleaning conventions" in f.lower()


def test_create_skill_via_tool(server):
    s = call(
        server,
        "keel_create_skill",
        {"skill_id": "mcp-made", "description": "Demo. Use when testing."},
    )
    assert s["id"] == "mcp-made"


# ─── error surfacing ─────────────────────────────────────────────────────────


def test_missing_task_raises_tool_error(server):
    # A KeelError inside a tool surfaces as a ToolError to the client.
    with pytest.raises(Exception) as excinfo:
        asyncio.run(server.call_tool("keel_get_task", {"task_id": "TEST-404-ghost"}))
    assert "not found" in str(excinfo.value).lower()


# ─── root resolution ─────────────────────────────────────────────────────────


def test_resolve_root_explicit(project_layout: Path):
    assert resolve_root(str(project_layout)) == project_layout


def test_resolve_root_rejects_non_repo(tmp_path: Path):
    with pytest.raises(SystemExit):
        resolve_root(str(tmp_path))
