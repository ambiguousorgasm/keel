"""Tests for `keel init` project scaffolding (keel.scaffold)."""

from __future__ import annotations

from pathlib import Path

import pytest

from keel.api import KeelRepo  # type: ignore[import-not-found]
from keel.errors import KeelError, ValidationError  # type: ignore[import-not-found]
from keel.scaffold import (  # type: ignore[import-not-found]
    build_template_archive,
    init_project,
    materialize_template,
)

# The live _keel/ template root (this test file is at _keel/tests/test_scaffold.py).
TEMPLATE_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def template_env(monkeypatch):
    """Force template resolution to use the live _keel/ via the env override,
    so tests don't depend on whether the bundled zip was built."""
    monkeypatch.setenv("KEEL_TEMPLATE_ROOT", str(TEMPLATE_ROOT))


# ─── template materialization ────────────────────────────────────────────────


def test_materialize_from_env(tmp_path: Path, template_env):
    dest = tmp_path / "proj" / "_keel"
    src = materialize_template(dest)
    assert src.startswith("env:")
    assert (dest / "BOOTSTRAP.md").is_file()
    assert (dest / "templates").is_dir()
    assert (dest / "skills").is_dir()
    # excluded junk must not be copied
    assert not (dest / "tests").exists()
    assert not (dest / "scripts" / "keel" / "assets").exists()


def test_materialize_refuses_existing(tmp_path: Path, template_env):
    dest = tmp_path / "_keel"
    dest.mkdir()
    with pytest.raises(KeelError):
        materialize_template(dest)


def test_build_template_archive_is_clean(tmp_path: Path):
    import zipfile
    dest_zip = tmp_path / "t.zip"
    n = build_template_archive(TEMPLATE_ROOT, dest_zip)
    assert n > 0
    names = zipfile.ZipFile(dest_zip).namelist()
    assert any(x == "BOOTSTRAP.md" for x in names)
    assert not any(x.startswith("tests/") for x in names)
    assert not any("assets" in x for x in names)  # non-recursive


# ─── init_project ────────────────────────────────────────────────────────────


def test_init_creates_valid_project(tmp_path: Path, template_env):
    root = tmp_path / "neworder"
    result = init_project(
        root, name="New Order", prefix="NORD", runner="just", git=False, write_env=True
    )
    assert result.root == root.resolve()
    assert (root / "_keel" / "spec_model.yml").is_file()
    assert (root / "PROJECT_SPEC.md").is_file()
    assert (root / "justfile").is_file()
    assert (root / ".gitignore").is_file()
    assert (root / ".env.example").is_file()
    for sub in ("active", "completed", "blocked"):
        assert (root / "tasks" / sub).is_dir()


def test_init_placeholder_spec_is_schema_valid(tmp_path: Path, template_env):
    root = tmp_path / "valid"
    init_project(root, name="Valid", prefix="VAL", git=False)
    # The whole point of the placeholder: doctor/info work immediately.
    repo = KeelRepo(root)
    model = repo.get_spec_model(validate=True)  # raises if invalid
    assert model["project_prefix"] == "VAL"
    assert model["project_name"] == "Valid"


def test_init_makefile_runner(tmp_path: Path, template_env):
    root = tmp_path / "mk"
    init_project(root, name="Mk", prefix="MK", runner="make", git=False)
    assert (root / "Makefile").is_file()
    assert not (root / "justfile").exists()


def test_init_rejects_bad_prefix(tmp_path: Path, template_env):
    with pytest.raises(ValidationError):
        init_project(tmp_path / "x", name="X", prefix="lowercase", git=False)


def test_init_rejects_nonempty_dir(tmp_path: Path, template_env):
    root = tmp_path / "occupied"
    root.mkdir()
    (root / "something.txt").write_text("hi")
    with pytest.raises(KeelError):
        init_project(root, name="X", prefix="XX", git=False)


def test_init_force_into_nonempty(tmp_path: Path, template_env):
    root = tmp_path / "occupied2"
    root.mkdir()
    (root / "keep.txt").write_text("hi")
    init_project(root, name="X", prefix="XX", git=False, force=True)
    assert (root / "_keel").is_dir()
    assert (root / "keep.txt").is_file()  # didn't clobber existing files


def test_project_spec_is_filled(tmp_path: Path, template_env):
    root = tmp_path / "filled"
    init_project(root, name="Cool Thing", prefix="COOL", git=False)
    spec = (root / "PROJECT_SPEC.md").read_text()
    assert "Cool Thing" in spec
    assert "COOL" in spec


# ─── prefix derivation (used by interactive mode) ────────────────────────────


def test_derive_prefix():
    from keel.main import _derive_prefix
    assert _derive_prefix("Order Pipeline") == "OP"
    assert _derive_prefix("checkout") == "CHEC"
    assert _derive_prefix("a-b-c service") == "ABCS"
    # never empty, always >= 2 chars
    assert len(_derive_prefix("x")) >= 2


def test_parse_spec_identity():
    from keel.scaffold import parse_spec_identity
    text = "# Order Pipeline — Design Spec\n\n**Project name:** Order Pipeline\n**Project prefix:** ORDP\n"
    name, prefix = parse_spec_identity(text)
    assert name == "Order Pipeline"
    assert prefix == "ORDP"


def test_parse_spec_identity_ignores_placeholders():
    from keel.scaffold import parse_spec_identity
    text = "# <Project Name> — Design Spec\n**Project name:** <full name>\n"
    name, prefix = parse_spec_identity(text)
    assert name is None and prefix is None


def test_init_from_spec_file(tmp_path: Path, template_env):
    spec = tmp_path / "myspec.md"
    spec.write_text(
        "# Cool Service — Design Spec\n\n**Project name:** Cool Service\n"
        "**Project prefix:** COOL\n\n## Purpose\nDo cool things.\n"
    )
    root = tmp_path / "cool"
    init_project(root, name="Cool Service", prefix="COOL", git=False, spec_file=spec)
    written = (root / "PROJECT_SPEC.md").read_text()
    assert "Do cool things." in written  # used the provided spec, not the skeleton


def test_init_rejects_missing_spec_file(tmp_path: Path, template_env):
    with pytest.raises(KeelError):
        init_project(tmp_path / "x", name="X", prefix="XX", git=False,
                     spec_file=tmp_path / "does-not-exist.md")
