"""KEEL skills — a tool-agnostic, filesystem-based skill system.

A "skill" is a folder under `_keel/skills/` containing a `SKILL.md` file:

    _keel/skills/
        my-skill/
            SKILL.md            # required: YAML frontmatter + markdown body
            scripts/            # optional bundled files
                helper.py
            references/
                cheatsheet.md

`SKILL.md` looks like:

    ---
    name: My Skill
    description: >
      One or two sentences on what this does AND when to use it. This text is
      what an agent surveys to decide whether to load the full skill.
    version: 0.1
    keywords: [example, demo]
    ---

    # My Skill

    Full instructions go here...

Design follows Claude-style *progressive disclosure*:

- `list_skills()` reads only frontmatter — cheap to survey many skills.
- `load_skill()` reads the full body and enumerates bundled files.
- bundled files are read on demand via `load_skill_file()`.

KEEL is the registry and loader. It does NOT execute bundled scripts or decide
when a skill fires — that stays with whatever agent consumes the skill, which
keeps the system open and tool-neutral.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .errors import SkillExists, SkillNotFound, SkillValidationError

SKILL_FILE = "SKILL.md"
_SKIP_NAMES = {"__pycache__", ".DS_Store"}
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
_KEBAB_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


# ─── data types ──────────────────────────────────────────────────────────────


@dataclass
class SkillInfo:
    """Lightweight skill metadata — frontmatter only (progressive disclosure)."""

    id: str
    name: str
    description: str
    version: str | None
    keywords: list[str]
    path: Path
    manual_only: bool = False
    export: bool = True
    bundled_files: list[str] = field(default_factory=list)


@dataclass
class Skill(SkillInfo):
    """A fully-loaded skill: metadata plus the markdown body."""

    body: str = ""

    def render(self) -> str:
        """Return the skill body, suitable for injecting into an agent prompt."""
        return self.body


# ─── frontmatter parsing ─────────────────────────────────────────────────────


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split a SKILL.md into (frontmatter_dict, body).

    Raises SkillValidationError if the frontmatter block is absent or invalid.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise SkillValidationError(
            "SKILL.md must begin with a YAML frontmatter block delimited by '---'."
        )
    raw, body = m.group(1), m.group(2)
    try:
        meta = yaml.safe_load(raw) or {}
    except yaml.YAMLError as e:
        raise SkillValidationError(f"frontmatter is not valid YAML: {e}") from e
    if not isinstance(meta, dict):
        raise SkillValidationError("frontmatter must be a mapping (key: value).")
    return meta, body.strip() + "\n"


def _validate_meta(meta: dict[str, Any], skill_id: str) -> None:
    """Validate required frontmatter fields. Raises SkillValidationError."""
    name = meta.get("name")
    if not isinstance(name, str) or not name.strip():
        raise SkillValidationError(f"skill {skill_id!r}: 'name' is required and non-empty.")
    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        raise SkillValidationError(
            f"skill {skill_id!r}: 'description' is required and non-empty. "
            f"It is the text agents use to decide whether to load this skill."
        )
    declared_id = meta.get("id")
    if declared_id is not None and declared_id != skill_id:
        raise SkillValidationError(
            f"skill folder is {skill_id!r} but frontmatter declares id {declared_id!r}; "
            f"they must match (or omit 'id')."
        )
    for flag in ("manual_only", "export"):
        if flag in meta and not isinstance(meta[flag], bool):
            raise SkillValidationError(
                f"skill {skill_id!r}: {flag!r} must be a boolean (true/false) if present."
            )


# ─── discovery ───────────────────────────────────────────────────────────────


def _bundled_files(skill_dir: Path) -> list[str]:
    """Relative paths of all files in the skill folder except SKILL.md."""
    out: list[str] = []
    for p in sorted(skill_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.name == SKILL_FILE:
            continue
        if any(part in _SKIP_NAMES for part in p.parts):
            continue
        out.append(p.relative_to(skill_dir).as_posix())
    return out


def _read_info(skill_dir: Path) -> SkillInfo:
    skill_id = skill_dir.name
    skill_file = skill_dir / SKILL_FILE
    if not skill_file.is_file():
        raise SkillValidationError(f"{skill_dir} has no {SKILL_FILE}.")
    meta, _body = parse_frontmatter(skill_file.read_text())
    _validate_meta(meta, skill_id)
    keywords = meta.get("keywords") or []
    if not isinstance(keywords, list):
        keywords = [str(keywords)]
    version = meta.get("version")
    return SkillInfo(
        id=skill_id,
        name=str(meta["name"]).strip(),
        description=str(meta["description"]).strip(),
        version=str(version) if version is not None else None,
        keywords=[str(k) for k in keywords],
        path=skill_dir,
        manual_only=bool(meta.get("manual_only", False)),
        export=bool(meta.get("export", True)),
        bundled_files=_bundled_files(skill_dir),
    )


def list_skills(skills_dir: Path) -> list[SkillInfo]:
    """Return SkillInfo for every valid skill folder under `skills_dir`.

    A skill folder is any directory containing a SKILL.md. Non-skill entries
    (loose files like README.md, or folders without SKILL.md) are ignored.
    Invalid skills raise — a malformed skill should be visible, not silently
    dropped — but the error names the offending folder.
    """
    if not skills_dir.is_dir():
        return []
    infos: list[SkillInfo] = []
    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_dir() or entry.name in _SKIP_NAMES:
            continue
        if not (entry / SKILL_FILE).is_file():
            continue  # not a skill folder
        infos.append(_read_info(entry))
    return infos


def load_skill(skills_dir: Path, skill_id: str) -> Skill:
    """Fully load one skill (frontmatter + body). Raises SkillNotFound."""
    skill_dir = skills_dir / skill_id
    skill_file = skill_dir / SKILL_FILE
    if not skill_file.is_file():
        raise SkillNotFound(f"skill {skill_id!r} not found at {skill_dir}.")
    meta, body = parse_frontmatter(skill_file.read_text())
    _validate_meta(meta, skill_id)
    info = _read_info(skill_dir)
    return Skill(
        id=info.id,
        name=info.name,
        description=info.description,
        version=info.version,
        keywords=info.keywords,
        path=info.path,
        manual_only=info.manual_only,
        export=info.export,
        bundled_files=info.bundled_files,
        body=body,
    )


def load_skill_file(skills_dir: Path, skill_id: str, relpath: str) -> str:
    """Read a bundled file inside a skill folder. Raises SkillNotFound."""
    skill_dir = skills_dir / skill_id
    if not (skill_dir / SKILL_FILE).is_file():
        raise SkillNotFound(f"skill {skill_id!r} not found.")
    target = (skill_dir / relpath).resolve()
    # Prevent path traversal outside the skill folder.
    if not str(target).startswith(str(skill_dir.resolve())):
        raise SkillNotFound(f"{relpath!r} is outside skill {skill_id!r}.")
    if not target.is_file():
        raise SkillNotFound(f"{relpath!r} not found in skill {skill_id!r}.")
    return target.read_text()


def search_skills(skills_dir: Path, query: str) -> list[SkillInfo]:
    """Case-insensitive match of `query` against id, name, description, keywords."""
    q = query.lower().strip()
    hits: list[SkillInfo] = []
    for info in list_skills(skills_dir):
        haystack = " ".join(
            [info.id, info.name, info.description, " ".join(info.keywords)]
        ).lower()
        if q in haystack:
            hits.append(info)
    return hits


def skills_index(skills_dir: Path) -> str:
    """A compact markdown index (id + description) for injecting into a prompt.

    This is the progressive-disclosure entry point: give an agent THIS, not the
    full body of every skill, and let it pull full skills on demand.
    """
    infos = list_skills(skills_dir)
    if not infos:
        return "_No skills installed._\n"
    lines = ["# Available skills\n"]
    for info in infos:
        desc = " ".join(info.description.split())
        lines.append(f"- **{info.id}** — {desc}")
    return "\n".join(lines) + "\n"


# ─── Agent Skills bridge (.agents/skills/) ───────────────────────────────────
#
# KEEL keeps skills canonically under `_keel/skills/` so they travel with the
# OS and update cleanly. But agent tools (Zed, Claude Code, Codex, Cursor,
# Gemini, ...) discover skills via the portable Agent Skills convention:
#
#     <repo>/.agents/skills/<name>/SKILL.md
#
# `sync` GENERATES that tree from the canonical skills so there is exactly one
# source of truth. The mirror is a build artifact: it carries a DO-NOT-EDIT
# banner, and `lint` reports drift. We translate KEEL frontmatter to the
# portable fields those tools read:
#
#     name  := the KEEL skill id (also the folder name, per the convention)
#     description := the KEEL description (the routing metadata)
#     disable-model-invocation: true  ← emitted when manual_only is set
#
# We only ever create/refresh/remove mirrors we generated (identified by the
# banner). Hand-authored skills a user drops into `.agents/skills/` are left
# untouched.

_MANAGED_MARKER = "GENERATED from _keel/skills/"


def render_agent_skill(skill: Skill) -> str:
    """Render a canonical KEEL Skill as a portable Agent Skills `SKILL.md`."""
    desc = " ".join(skill.description.split())
    lines = ["---", f"name: {skill.id}", "description: >", f"  {desc}"]
    if skill.manual_only:
        # The portable, cross-tool flag for "never run autonomously".
        lines.append("disable-model-invocation: true")
    lines.append("---")
    banner = (
        f"<!-- {_MANAGED_MARKER}{skill.id}/SKILL.md by `keel skills sync` — "
        f"DO NOT EDIT HERE. Edit the canonical skill, then re-run sync. -->"
    )
    return "\n".join(lines) + "\n\n" + banner + "\n\n" + skill.body.lstrip("\n")


def export_agent_skills(skills_dir: Path, agents_skills_dir: Path) -> dict[str, list[str]]:
    """Generate `.agents/skills/` mirrors from canonical skills.

    Returns {"written": [...ids], "removed": [...stale ids]}. Only mirrors
    KEEL generated (carrying the banner) are ever removed; hand-authored skills
    in the same directory are preserved.
    """
    infos = list_skills(skills_dir)
    exported_ids = {i.id for i in infos if i.export}
    agents_skills_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    for info in infos:
        if not info.export:
            continue
        skill = load_skill(skills_dir, info.id)
        dest = agents_skills_dir / skill.id
        dest.mkdir(parents=True, exist_ok=True)
        (dest / SKILL_FILE).write_text(render_agent_skill(skill))
        for rel in skill.bundled_files:
            src = skill.path / rel
            tgt = dest / rel
            tgt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, tgt)
        written.append(skill.id)

    # Remove stale mirrors we previously generated (skill deleted or no longer
    # exported). Never touch a directory we didn't generate.
    removed: list[str] = []
    if agents_skills_dir.is_dir():
        for entry in sorted(agents_skills_dir.iterdir()):
            if not entry.is_dir() or entry.name in exported_ids:
                continue
            mirror = entry / SKILL_FILE
            if mirror.is_file() and _MANAGED_MARKER in mirror.read_text():
                shutil.rmtree(entry)
                removed.append(entry.name)

    return {"written": sorted(written), "removed": sorted(removed)}


def render_catalog(skills_dir: Path) -> str:
    """Render `.agents/SKILLS.md` — a human-readable catalog, NOT a rule source."""
    infos = list_skills(skills_dir)
    out = [
        "# Skill catalog",
        "",
        "> GENERATED by `keel skills sync`. A human-readable index of this",
        "> project's skills. Canonical skills live in `_keel/skills/`; the",
        "> agent-discoverable mirrors are generated into `.agents/skills/`.",
        "> This is a catalog, not a second source of workflow rules — each",
        "> skill's `SKILL.md` body remains the source of truth.",
        "",
    ]
    if not infos:
        out.append("_No skills installed._")
        return "\n".join(out) + "\n"
    out += [
        "| Skill | Invocation | Discoverable | Purpose & triggers |",
        "|---|---|---|---|",
    ]
    for i in infos:
        mode = "manual-only" if i.manual_only else "auto"
        disc = "—" if not i.export else "`.agents/skills/`"
        desc = " ".join(i.description.split())
        out.append(f"| `{i.id}` | {mode} | {disc} | {desc} |")
    out += [
        "",
        "**Invocation.** `auto` skills may be selected automatically by an agent "
        "when the task matches the description. `manual-only` skills are exported "
        "with `disable-model-invocation: true` and must be invoked deliberately "
        "(e.g. a slash command) — an agent will not run them on its own.",
        "",
        "Canonical source for every skill: `_keel/skills/<id>/SKILL.md`. "
        "Regenerate this catalog and the mirrors with `keel skills sync`.",
    ]
    return "\n".join(out) + "\n"


def lint_skills(
    skills_dir: Path,
    agents_skills_dir: Path | None = None,
    catalog_path: Path | None = None,
) -> list[str]:
    """Validate the skill library. Returns a list of problems ([] == clean).

    Checks: frontmatter validity, duplicate names, empty descriptions,
    manual-only safeguard present in the mirror, and mirror/catalog drift.
    Collects problems rather than raising, so one bad skill doesn't hide others.
    """
    problems: list[str] = []
    if not skills_dir.is_dir():
        return [f"skills directory not found: {skills_dir}"]

    infos: list[SkillInfo] = []
    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_dir() or entry.name in _SKIP_NAMES:
            continue
        if not (entry / SKILL_FILE).is_file():
            continue
        try:
            infos.append(_read_info(entry))
        except SkillValidationError as e:
            problems.append(f"{entry.name}: {e}")

    # duplicate display names (collide in a tool's catalog)
    seen: dict[str, str] = {}
    for i in infos:
        key = i.name.lower()
        if key in seen:
            problems.append(
                f"duplicate skill name {i.name!r}: used by {seen[key]!r} and {i.id!r}"
            )
        else:
            seen[key] = i.id

    # mirror drift + manual-only safeguard
    if agents_skills_dir is not None:
        for i in infos:
            if not i.export:
                continue
            mirror = agents_skills_dir / i.id / SKILL_FILE
            if not mirror.is_file():
                problems.append(
                    f"{i.id}: no mirror at .agents/skills/{i.id}/ — run `keel skills sync`"
                )
                continue
            expected = render_agent_skill(load_skill(skills_dir, i.id))
            if mirror.read_text() != expected:
                problems.append(
                    f"{i.id}: .agents mirror is out of date — run `keel skills sync`"
                )
            if i.manual_only and "disable-model-invocation: true" not in mirror.read_text():
                problems.append(
                    f"{i.id}: manual-only skill is missing its safeguard "
                    f"(disable-model-invocation) in the mirror"
                )

    # catalog references resolve to real skills
    if catalog_path is not None and catalog_path.is_file():
        ids = {i.id for i in infos}
        referenced = set(re.findall(r"`([a-z0-9][a-z0-9-]*)`", catalog_path.read_text()))
        # only flag tokens that look like skill ids we manage and that vanished
        for ref in sorted(referenced):
            if ref.startswith("dev-") and ref not in ids:
                problems.append(f"catalog references unknown skill {ref!r}")

    return problems


# ─── scaffolding ─────────────────────────────────────────────────────────────


def create_skill(
    skills_dir: Path,
    skill_id: str,
    *,
    name: str | None = None,
    description: str | None = None,
    template: Path | None = None,
) -> Skill:
    """Scaffold a new skill folder + SKILL.md. Returns the loaded Skill.

    `template`, if given, is a SKILL.md template whose `{{ID}}`, `{{NAME}}`, and
    `{{DESCRIPTION}}` placeholders are substituted. Otherwise a minimal default
    is written.
    """
    if not _KEBAB_RE.fullmatch(skill_id):
        raise SkillValidationError(
            f"skill id {skill_id!r} must be kebab-case "
            f"(lowercase letters/digits, hyphen-separated)."
        )
    skill_dir = skills_dir / skill_id
    if skill_dir.exists():
        raise SkillExists(f"{skill_dir} already exists.")

    name = name or skill_id.replace("-", " ").title()
    description = description or (
        "TODO: one or two sentences on what this does AND when to use it."
    )
    # Quote the name if it contains characters that break a plain YAML scalar.
    safe_name = name
    if any(c in name for c in ":#") or name.strip() != name:
        safe_name = '"' + name.replace('"', '\\"') + '"'

    if template and template.is_file():
        text = (
            template.read_text()
            .replace("{{ID}}", skill_id)
            .replace("{{NAME}}", safe_name)
            .replace("{{DESCRIPTION}}", description)
        )
    else:
        text = (
            "---\n"
            f"name: {safe_name}\n"
            f"description: >\n  {description}\n"
            "version: 0.1\n"
            "keywords: []\n"
            "---\n\n"
            f"# {name}\n\n"
            "Full instructions for the agent go here.\n"
        )

    skill_dir.mkdir(parents=True)
    (skill_dir / SKILL_FILE).write_text(text)
    return load_skill(skills_dir, skill_id)
