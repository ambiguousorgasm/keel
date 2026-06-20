# KEEL MCP Server

Exposes the KEEL workflow — tasks, skills, and governance — as MCP tools, so any
MCP-aware agent (Claude Code, Claude Desktop, Cursor, custom clients) can drive
KEEL natively instead of shelling out.

This is **Layer 2**: a thin, stateless wrapper over the `keel.api.KeelRepo`
Python API. It adds no state and no orchestration. Every tool call is a repo
operation, and the repository stays the single source of truth.

## Install

The MCP server needs the optional `mcp` dependency:

```bash
pip install -e '_keel[mcp]'
```

This enables the `keel mcp` subcommand and pins `mcp>=1.27,<2` (below the
v2 line, which is in beta as of mid-2026).

## Run

The server binds to **one** project, resolved at startup in this order:

1. `--root /path/to/repo`
2. the `KEEL_ROOT` environment variable
3. discovery: walk up from the current directory to find `_keel/`

```bash
keel mcp --root /path/to/repo          # stdio (for Claude Desktop / Code)
keel mcp --transport streamable-http   # remote / HTTP clients
```

## Wire into Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "keel": {
      "command": "keel",
      "args": ["mcp", "--root", "/absolute/path/to/your/repo"]
    }
  }
}
```

If `keel mcp` isn't on Claude Desktop's PATH, use the full interpreter form:

```json
{
  "mcpServers": {
    "keel": {
      "command": "python",
      "args": ["-m", "keel.mcp_server", "--root", "/absolute/path/to/your/repo"],
      "env": { "PYTHONPATH": "/absolute/path/to/your/repo/_keel/scripts" }
    }
  }
}
```

(The second form works without `pip install` — it points `PYTHONPATH` at the
in-repo package.)

## Wire into Claude Code

Claude Code reads MCP servers from its settings. Add an entry pointing at
`keel mcp` with `--root` set to the project, or rely on `KEEL_ROOT`/CWD discovery
if Claude Code launches the server from inside the repo.

## Tool catalog (17 tools)

**Orientation**
- `keel_project_info` — name, prefix, phases, governance docs present. Call first.

**Tasks**
- `keel_list_tasks(state?)` — list packets; `state` ∈ active/completed/blocked.
- `keel_get_task(task_id)` — one packet's metadata.
- `keel_read_task_file(task_id, filename)` — read brief/plan/context/review/handoff.
- `keel_create_task(slug, task_type?, prefix_override?)` — scaffold a packet.
- `keel_build_context(task_id)` — generate `context.md` (verbatim, cache-ordered).
- `keel_verify_task(task_id)` — run the gates (checks + scenarios + scope).

**Governance**
- `keel_read_governance(name)` — verbatim doc (PRINCIPLES/CORE/COMPONENTS/…).
- `keel_list_governance()` — which governance docs exist.
- `keel_get_spec_model()` — the structured, schema-validated project model.
- `keel_update_code_map()` — refresh `docs/code-map/`.

**Skills** (progressive disclosure)
- `keel_skills_index()` — compact id+description list. **Call this first.**
- `keel_list_skills()` — full metadata per skill.
- `keel_get_skill(skill_id)` — load one skill's full instruction body.
- `keel_search_skills(query)` — match id/name/description/keywords.
- `keel_load_skill_file(skill_id, relpath)` — read a bundled file (traversal-guarded).
- `keel_create_skill(skill_id, name?, description?)` — scaffold a new skill.

## Design notes for integrators

- **Stateless & repo-canonical.** The server holds only the project location;
  every tool re-reads files. Run one server per project — that's the intended
  scope, mirroring how MCP servers are normally bound.
- **Writes are real and immediate.** `keel_create_task`, `keel_build_context`,
  `keel_verify_task`, `keel_create_skill`, and `keel_update_code_map` write to
  disk on the call. Per the project's "trust the gates" policy there is no
  preview step — the gates in `keel_verify_task` are the safety mechanism, and
  they're identical to the CLI's.
- **`keel_verify_task` shells out.** It runs the commands in `acceptance.yml`.
  Run the server against a working tree you trust, or sandbox it, if the calling
  agent is untrusted.
- **Errors are clean.** A `KeelError` inside a tool surfaces to the client as a
  tool error with a plain message — no KEEL-internal traceback.
- **Progressive disclosure for skills.** Point the agent at `keel_skills_index`
  first; it pulls a full skill body only when one is relevant.

## Testing the server

```bash
pip install -e '_keel[mcp]' pytest
pytest _keel/tests/test_mcp_server.py
```

The tests build the server in-process and call tools through the real MCP
machinery (`call_tool`), so they exercise schema generation, serialization, and
error wrapping without a separate client. They skip automatically if `mcp` isn't
installed.

## Debugging with the MCP Inspector

The MCP SDK ships an inspector for poking at a server interactively:

```bash
mcp dev keel mcp          # or: npx @modelcontextprotocol/inspector keel mcp
```
