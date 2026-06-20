# keel.spec — PyInstaller build specification
#
# Build the standalone keel executable:
#   cd _keel/
#   pyinstaller keel.spec
#
# Output:
#   dist/keel          (single-file executable on Linux/macOS)
#   dist/keel.exe      (on Windows)
#
# The executable embeds:
#   - the full keel Python package
#   - pyyaml and jsonschema (+ referencing) 
#   - the bundled _keel template zip (so `keel init` creates new projects)
#
# NOT included: the optional mcp server deps (uvicorn, starlette, pydantic, httpx).
# The `keel mcp` subcommand will print a helpful error if invoked from the bundle.
# Run MCP from a pip-installed environment if you need it.
#
# After building, copy the executable wherever you want — no Python installation
# required on the target machine.

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from pathlib import Path

block_cipher = None

# ── hidden imports ────────────────────────────────────────────────────────────
# PyInstaller's static analysis misses dynamic imports in jsonschema 4.x and
# referencing. Declare them all explicitly.

hidden = [
    # keel package — all submodules
    "keel",
    "keel.api",
    "keel.errors",
    "keel.helpers",
    "keel.main",
    "keel.mcp_server",
    "keel.operations",
    "keel.scaffold",
    "keel.skills",

    # pyyaml
    "yaml",
    "_yaml",

    # jsonschema 4.x core — dynamically imported at runtime
    "jsonschema",
    "jsonschema.validators",
    "jsonschema.exceptions",
    "jsonschema.protocols",
    "jsonschema._format",
    "jsonschema._keywords",
    "jsonschema._legacy_keywords",
    "jsonschema._types",
    "jsonschema._typing",
    "jsonschema._utils",

    # referencing — jsonschema 4.x depends on this for $ref resolution
    "referencing",
    "referencing._attrs",
    "referencing._core",
    "referencing.exceptions",
    "referencing.jsonschema",
    "referencing.retrieval",
    "referencing.typing",

    # attrs — referencing depends on this
    "attr",
    "attrs",
]

# ── data files ────────────────────────────────────────────────────────────────
# The bundled template zip must travel with the executable.
# scaffold.py resolves it as: Path(__file__).parent / "assets" / "keel_template.zip"
# __file__ in the bundle is <MEIPASS>/keel/scaffold.py, so dest must be "keel/assets".

datas = [
    (
        str(Path("scripts/keel/assets/keel_template.zip").resolve()),
        "keel/assets",
    ),
]

# ── analysis ──────────────────────────────────────────────────────────────────

a = Analysis(
    ["main.py"],                         # entry point: _keel/main.py
    pathex=[str(Path("scripts").resolve())],  # so PyInstaller finds the keel package
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # exclude the heavy MCP stack — keel mcp gracefully errors if unavailable
        "mcp",
        "uvicorn",
        "starlette",
        "pydantic",
        "httpx",
        "httpcore",
        "h11",
        "anyio",
        "sniffio",
        # exclude dev/test-only deps
        "pytest",
        "pyflakes",
        "pip",
        "setuptools",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── single-file executable ────────────────────────────────────────────────────

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="keel",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,          # compress if UPX is available; set False if it isn't
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,       # keel is a terminal tool
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,          # add a .ico/.icns path here if you want an icon
)
