---
name: "Dev: Build Context"
id: dev-build-context
description: >
  Generate a task's context.md by running KEEL's deterministic, verbatim, cache-ordered context builder. Use once a plan is approved, before implementation starts.
version: 1.0
keywords: [keel, workflow, builtin]
---

# /dev-build-context

**Role:** context builder. Runs the deterministic context script.

**prompt_version:** 1.0

**Usage:** `/dev-build-context <task_id>`

---

Run `just build-context $ARGUMENTS` (or equivalently
`python _keel/scripts/agent/build_context.py $ARGUMENTS`).

If the command exits non-zero, surface the error verbatim. Do NOT attempt to
hand-assemble `context.md` — it must be the deterministic output of the script.

After it succeeds, read the generated `tasks/active/$ARGUMENTS/context.md`
top-to-bottom so the human can see you've absorbed it. Then stop.

If a Relevant-source reference produced a `⚠ build_context:` warning in the
output (heading not found, id not found, file missing), flag this to the human
and propose either (a) fixing the brief's references or (b) updating the source
document. Do not silently move past warnings.

## Trace

After the script runs, the trace is already appended by the script itself. You
do not need to add another entry unless you encountered a warning, in which case
append:

```json
{"role": "context_builder", "action": "warnings_surfaced", "task_id": "$ARGUMENTS", "prompt_version": "dev-build-context@1.0", "warnings": ["..."]}
```
