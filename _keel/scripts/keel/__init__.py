"""KEEL — repo-native agent development OS.

Public Python API:

    from keel import KeelRepo
    repo = KeelRepo.discover()

All errors derive from keel.KeelError.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .api import (
    GOVERNANCE_DOCS,
    KeelRepo,
    TaskInfo,
)
from .errors import (
    GovernanceNotFound,
    KeelError,
    ProjectNotFound,
    SkillError,
    SkillExists,
    SkillNotFound,
    SkillValidationError,
    SpecModelError,
    TaskExists,
    TaskNotFound,
    TemplateError,
    ValidationError,
)
from .operations import (
    CheckResult,
    CodeMapResult,
    ContextResult,
    CreatedTask,
    VerificationResult,
)
from .skills import Skill, SkillInfo

__all__ = [
    "KeelRepo",
    "TaskInfo",
    "GOVERNANCE_DOCS",
    "Skill",
    "SkillInfo",
    "KeelError",
    "ProjectNotFound",
    "SpecModelError",
    "TaskNotFound",
    "TaskExists",
    "ValidationError",
    "TemplateError",
    "GovernanceNotFound",
    "SkillError",
    "SkillNotFound",
    "SkillValidationError",
    "SkillExists",
    "CheckResult",
    "CodeMapResult",
    "ContextResult",
    "CreatedTask",
    "VerificationResult",
]
