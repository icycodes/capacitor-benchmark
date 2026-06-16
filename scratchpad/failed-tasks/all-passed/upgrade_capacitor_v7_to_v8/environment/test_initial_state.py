import json
import os
import re
import shutil
import subprocess

PROJECT_DIR = "/home/user/myapp"
SNAPSHOT_PATH = "/home/user/.harbor/initial_capacitor_config.json"


def _parse_major(version_string: str) -> int:
    """Parse the major version from an npm version string or range."""
    assert isinstance(version_string, str), (
        f"Expected version to be a string, got {type(version_string).__name__}."
    )
    cleaned = version_string.strip()
    for prefix in (">=", "<=", "==", "^", "~", ">", "<", "="):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].lstrip()
            break
    if cleaned.startswith("v") or cleaned.startswith("V"):
        cleaned = cleaned[1:]
    match = re.match(r"(\d+)", cleaned)
    assert match is not None, (
        f"Could not parse a major version number from version string {version_string!r}."
    )
    return int(match.group(1))


# ---------------------------------------------------------------------------
# Toolchain availability
# ---------------------------------------------------------------------------


def test_node_available():
    assert shutil.which("node") is not None, "Node.js binary is not available in PATH."


def test_node_version_is_22_or_higher():
    result = subprocess.run(["node", "--version"], capture_output=True, text=True)
    assert result.returncode == 0, f"`node --version` failed: {result.stderr}"
    raw = result.stdout.strip()
    assert raw.startswith("v"), f"Unexpected node version output: {raw}"
    major = int(raw[1:].split(".")[0])
    assert major >= 22, f"Capacitor v8 requires Node.js >= 22, found {raw}."


def test_npm_available():
    assert shutil.which("npm") is not None, "npm binary is not available in PATH."


def test_npx_available():
    assert shutil.which("npx") is not None, "npx binary is not available in PATH."


# ---------------------------------------------------------------------------
# Project layout
# ---------------------------------------------------------------------------


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_package_json_exists():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg), f"package.json not found at {pkg}."


def test_package_json_is_valid_json():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    assert isinstance(data, dict), "package.json must contain a JSON object."
    assert "scripts" in data, "package.json must define a 'scripts' section."


def test_capacitor_config_file_present():
    cap_config = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    assert os.path.isfile(cap_config), (
        f"Expected the Capacitor configuration file at {cap_config}."
    )


def test_index_html_exists():
    html = os.path.join(PROJECT_DIR, "index.html")
    assert os.path.isfile(html), f"Expected the Vite entry HTML at {html}."


def test_node_modules_installed():
    nm = os.path.join(PROJECT_DIR, "node_modules")
    assert os.path.isdir(nm), (
        f"Expected dependencies to be pre-installed at {nm}. The task starts from "
        "an already-installed project."
    )


# ---------------------------------------------------------------------------
# Initial Capacitor packages MUST be declared on v7 (NOT v8) so the task is
# actually meaningful — the executor must perform the upgrade.
# ---------------------------------------------------------------------------


def _load_package_json():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg_path) as f:
        return json.load(f)


def test_capacitor_core_declared_on_v7():
    data = _load_package_json()
    deps = data.get("dependencies", {}) or {}
    assert "@capacitor/core" in deps, (
        "Expected '@capacitor/core' to be declared in dependencies in the initial state."
    )
    major = _parse_major(deps["@capacitor/core"])
    assert major == 7, (
        f"Expected '@capacitor/core' to start on the 7.x major, got "
        f"{deps['@capacitor/core']!r} (parsed major = {major})."
    )


def test_capacitor_preferences_declared_on_v7():
    data = _load_package_json()
    deps = data.get("dependencies", {}) or {}
    assert "@capacitor/preferences" in deps, (
        "Expected '@capacitor/preferences' to be declared in dependencies in the initial state."
    )
    major = _parse_major(deps["@capacitor/preferences"])
    assert major == 7, (
        f"Expected '@capacitor/preferences' to start on the 7.x major, got "
        f"{deps['@capacitor/preferences']!r} (parsed major = {major})."
    )


def test_capacitor_cli_declared_on_v7():
    data = _load_package_json()
    dev_deps = data.get("devDependencies", {}) or {}
    assert "@capacitor/cli" in dev_deps, (
        "Expected '@capacitor/cli' to be declared in devDependencies in the initial state."
    )
    major = _parse_major(dev_deps["@capacitor/cli"])
    assert major == 7, (
        f"Expected '@capacitor/cli' to start on the 7.x major, got "
        f"{dev_deps['@capacitor/cli']!r} (parsed major = {major})."
    )


def test_installed_capacitor_core_is_v7():
    p = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "core", "package.json")
    assert os.path.isfile(p), (
        f"Expected installed @capacitor/core package.json at {p}."
    )
    with open(p) as f:
        meta = json.load(f)
    version = meta.get("version")
    assert isinstance(version, str), (
        f"Expected installed @capacitor/core to have a string version, got {version!r}."
    )
    major = _parse_major(version)
    assert major == 7, (
        f"Expected installed @capacitor/core version to start on 7.x, got {version!r}."
    )


def test_installed_capacitor_cli_is_v7():
    p = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "cli", "package.json")
    assert os.path.isfile(p), (
        f"Expected installed @capacitor/cli package.json at {p}."
    )
    with open(p) as f:
        meta = json.load(f)
    version = meta.get("version")
    assert isinstance(version, str), (
        f"Expected installed @capacitor/cli to have a string version, got {version!r}."
    )
    major = _parse_major(version)
    assert major == 7, (
        f"Expected installed @capacitor/cli version to start on 7.x, got {version!r}."
    )


def test_installed_capacitor_preferences_is_v7():
    p = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "preferences", "package.json"
    )
    assert os.path.isfile(p), (
        f"Expected installed @capacitor/preferences package.json at {p}."
    )
    with open(p) as f:
        meta = json.load(f)
    version = meta.get("version")
    assert isinstance(version, str), (
        f"Expected installed @capacitor/preferences to have a string version, got {version!r}."
    )
    major = _parse_major(version)
    assert major == 7, (
        f"Expected installed @capacitor/preferences version to start on 7.x, got {version!r}."
    )


# ---------------------------------------------------------------------------
# The initial capacitor.config.ts snapshot file is what the verifier compares
# against to confirm the executor did not modify appId/appName/webDir.
# ---------------------------------------------------------------------------


def test_initial_capacitor_config_snapshot_present():
    assert os.path.isfile(SNAPSHOT_PATH), (
        f"Expected snapshot file {SNAPSHOT_PATH} to be written by the environment. "
        "The verifier needs this file to confirm the executor did not modify "
        "appId/appName/webDir."
    )
    with open(SNAPSHOT_PATH) as f:
        snap = json.load(f)
    for key in ("appId", "appName", "webDir"):
        assert key in snap, f"Snapshot file is missing required key {key!r}."
        assert isinstance(snap[key], str) and snap[key], (
            f"Snapshot value for {key!r} must be a non-empty string."
        )
