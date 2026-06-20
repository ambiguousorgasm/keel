"""KEEL exception hierarchy.

Library code raises these instead of SystemExit so that API callers can catch
and handle failures programmatically. The CLI wrappers translate these into
clean stderr messages + non-zero exit codes.
"""

from __future__ import annotations


class KeelError(Exception):
    """Base class for all KEEL errors. Catch this to handle any KEEL failure."""


class ProjectNotFound(KeelError):
    """No _keel/ directory found walking up from the start path."""


class SpecModelError(KeelError):
    """spec_model.yml is missing, unparseable, or fails schema validation."""


class TaskNotFound(KeelError):
    """A referenced task ID does not exist under tasks/{active,completed,blocked}."""


class TaskExists(KeelError):
    """A task directory already exists where a new one would be created."""


class ValidationError(KeelError):
    """An input failed validation (bad slug, unknown task type, etc.)."""


class TemplateError(KeelError):
    """A required template file is missing."""


class GovernanceNotFound(KeelError):
    """A requested governance document (CORE.md, PRINCIPLES.md, ...) is absent."""


class SkillError(KeelError):
    """Base for skill-related failures."""


class SkillNotFound(SkillError):
    """A referenced skill id does not exist under _keel/skills/."""


class SkillValidationError(SkillError):
    """A skill's SKILL.md is missing required frontmatter or is malformed."""


class SkillExists(SkillError):
    """A skill folder already exists where a new one would be created."""
