---
name: explain-clear
id: explain-clear
description: >
  On-demand comprehension modifier. When you hit a concept, subsystem, file,
  decision, or block of code you want unpacked more carefully, this expands the
  explanation at a controllable level — without talking down to you. Use it when
  you say things like "explain this more clearly", "I don't have the right mental
  model for X", "why does this exist", "trace the flow", "map the components",
  "translate this code", "what am I probably getting wrong about this", or invoke
  it directly as "/explain-clear [dials]: <question>". It assumes baseline
  technical literacy and surgically expands only what's needed to make the
  current thing intelligible — it does NOT restart from beginner programming.
version: 1.0
keywords: [explain, clarity, mental-model, comprehension, understanding, concepts]
---

# explain-clear

An **on-demand comprehension modifier**, not a teaching mode. The user is
technically engaged and has baseline programming literacy. They have hit a
specific concept, subsystem, file, decision, or piece of code they want a
*better mental model* of — expanded carefully, at a level they control, without
being talked down to.

## The two rules that define this skill

> **1. Don't restart from beginner programming.** Assume baseline technical
> literacy. Expand only the concepts necessary to make the *current* question
> intelligible, while preserving the project's actual terminology, constraints,
> and architecture. Never slow everything down by default.

> **2. Don't merely paraphrase. Find the missing link.** When the user asks for
> clarity, identify the specific mental link they're missing, then explain *that
> link* at the requested level of abstraction. Rephrasing the same sentence in
> different words is a failure of this skill. The value is in locating and
> filling the gap, not in restating what's already there.

Everything below is in service of those two rules.

## How it's invoked

Naturally, mid-work. All dials are **optional** — set only what you want to
steer; sensible defaults fill the rest, and the MODE usually implies them.

```
/explain-clear <dials, comma-separated>: <your question>
[Include: extra aspects, one per line or comma-separated]
```

Examples (all valid):

```
/explain-clear why does this exist?
```
```
/explain-clear deep, balanced, layered: Why an event queue here instead of
calling the agent directly?
Include: architecture reasoning, flow, tradeoffs, failure modes
```
```
/explain-clear concrete: Map the components involved in campaign ingestion.
Include: files/modules, data flow, extension points
```
```
/explain-clear deep, first-principles, guided: Why does state ownership matter
in this architecture?
```

Bare-language requests work too — "give me a deeper model of X", "trace how a
request flows through this" — map them onto the dials and modes below.

## The dials (all optional; named, not numeric)

**EXPANSION** — how much to unpack beyond a normal answer. *(main dial)*
- `light` — clarify only the confusing part.
- `moderate` — the concept plus its immediate dependencies. *(default)*
- `deep` — rebuild the mental model, including surrounding architecture.
- `full` (full excavation) — origins, components, flow, decisions, tradeoffs, edges.

**ABSTRACTION** — where the explanation should sit.
- `concrete` — files, functions, variables, requests, objects, rows.
- `balanced` — implementation plus conceptual model. *(default)*
- `conceptual` — architecture, patterns, design reasoning.
- `first-principles` — reduce to the underlying problem it solves.

**PACING** — how gradually it unfolds.
- `direct` — explain normally, only necessary context.
- `layered` — short answer first, then expand. *(default — preserves flow)*
- `stepwise` — one causal step at a time.
- `guided` — pause at likely confusion points and connect ideas explicitly.

**DENSITY** — how much technical language to retain.
- `plain-technical` — ordinary developer language; define unusual terms briefly.
- `standard` — normal technical vocabulary, no overexplaining. *(default)*
- `spec-level` — precise terminology, invariants, constraints, edge cases.
- `code-adjacent` — tie every concept back to concrete implementation detail.

If the user names a dial, honor it exactly. If not, use the default — OR the
value the chosen MODE implies (below), whichever is more specific.

## The modes (map to the kinds of confusion that happen while coding)

Each mode has a **shape** (what the answer should contain) and **implied dials**
(so you usually don't need to set them). The user's explicit dials always win.

### `what is this?` — a function/class/module/config/API/pattern
Shape: what it is · what problem it solves · where it fits · what calls/depends
on it · a small example.
Implied: moderate, balanced.

### `why does this exist?` — a choice that looks unnecessary or redundant
*(one of the most valuable modes)*
Shape: the original problem · the failure mode it prevents · alternatives ·
tradeoffs · what breaks or gets harder without it.
Implied: deep, conceptual; include tradeoffs + failure-modes.

### `trace the flow` — runtime behavior
Shape (in order): entry point → inputs → transformations → state changes →
external calls → output/side effects → error paths.
Implied: deep, concrete; include data-flow + state-changes.

### `map the components` — a subsystem or codebase area
Shape: main components · each one's responsibility · ownership boundaries ·
dependencies · data passed between them · key files/dirs · likely extension points.
Implied: moderate, balanced; include files/modules + dependencies.

### `translate this code` — a specific block or function
Shape: what each section does · why the order matters · important state changes ·
assumptions · hazards · a plain-English pseudocode version.
Optional toggle: `line-by-line`.
Implied: concrete, code-adjacent.

### `explain the design` — architecture / system-level
Shape: goal · constraints · chosen approach · alternatives rejected · tradeoffs ·
scaling/maintenance implications.
Implied: deep, conceptual; include tradeoffs.

### `debug the mental model` — when something feels contradictory
*(this is NOT code debugging — it means "explain what I'm probably assuming wrong")*
Shape: the likely mistaken intuition · the correct model · why the wrong model is
tempting · a concrete counterexample · a short rule of thumb.
Implied: deep, balanced; include misconceptions.

### `compare options` — async vs threading, SQLite vs Postgres, queue vs cron, …
Shape: shared purpose · main difference · when each wins · cost of choosing wrong ·
a recommendation *for this project specifically*.
Implied: balanced; include tradeoffs.

## INCLUDE toggles (driven by MODE; override or add via `Include:`)

The MODE preset pulls in the relevant ones automatically. Use an `Include:` block
only to add or override. Available aspects:

code examples · pseudocode · files/modules · data flow · call flow · state
changes · dependencies · alternatives · tradeoffs · failure modes · edge cases ·
common misconceptions · implementation steps · minimum viable version · how to
modify it safely · tests to verify understanding · ask one check question at the
end · keep it concise after the explanation.

Two worth calling out:
- **ask one check question at the end** — a single question that reveals whether
  the model landed. Off by default; on request.
- **keep it concise after the explanation** — give the deep explanation, then
  STOP. Don't trail into a tutorial. Respect this when set; many deep-expansion
  requests want depth *once*, not an ongoing lesson.

## Defaults when nothing is specified

`moderate` expansion · `balanced` abstraction · `layered` pacing · `standard`
density · MODE inferred from the question. Layered pacing means: lead with the
short answer, then expand — so the user reads only as far as they need.

## Anti-patterns

- **Paraphrasing instead of finding the gap.** The cardinal sin. If you're
  restating the same idea in new words, you haven't done the job.
- **Talking down.** This is a peer asking for a sharper model, not a student.
  No "as you may know," no re-teaching basics they clearly have.
- **Ignoring project reality.** Explain in terms of *this* codebase's actual
  names, constraints, and architecture — not a generic textbook version.
- **Over-expanding a `light` request.** If they asked to clarify one confusing
  part, clarify that part. Don't rebuild the universe.
- **Trailing into a tutorial** when `keep it concise after` is set (or implied by
  a busy working context).

See `references/modes.md` for worked examples of each mode and how the implied
dials play out.
