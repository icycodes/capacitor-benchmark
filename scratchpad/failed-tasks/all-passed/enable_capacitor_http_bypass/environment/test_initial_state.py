import json
import os
import shutil
import subprocess

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_node_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npm_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_npx_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH."


def test_node_version_at_least_22():
    result = subprocess.run(
        ["node", "--version"], capture_output=True, text=True, check=True
    )
    version_str = result.stdout.strip().lstrip("v")
    major = int(version_str.split(".")[0])
    assert major >= 22, (
        f"Capacitor v8 requires Node.js >= 22, found {result.stdout.strip()}."
    )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_package_json_exists():
    package_json = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(package_json), (
        f"package.json not found at {package_json}; the Capacitor project skeleton is incomplete."
    )


def test_package_json_has_capacitor_core_dependency():
    package_json = os.path.join(PROJECT_DIR, "package.json")
    with open(package_json) as f:
        pkg = json.load(f)
    deps = {}
    deps.update(pkg.get("dependencies", {}) or {})
    deps.update(pkg.get("devDependencies", {}) or {})
    assert "@capacitor/core" in deps, (
        "@capacitor/core dependency is missing from package.json."
    )
    assert "@capacitor/cli" in deps, (
        "@capacitor/cli dependency is missing from package.json."
    )


def test_capacitor_core_installed():
    capacitor_core = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "core")
    assert os.path.isdir(capacitor_core), (
        f"@capacitor/core is not installed in {capacitor_core}; run `npm install` during environment bootstrap."
    )


def test_capacitor_cli_installed():
    capacitor_cli_bin = os.path.join(
        PROJECT_DIR, "node_modules", ".bin", "cap"
    )
    assert os.path.isfile(capacitor_cli_bin) or os.path.islink(capacitor_cli_bin), (
        f"@capacitor/cli is not installed; expected executable at {capacitor_cli_bin}."
    )


def test_tsx_available_in_project():
    tsx_bin = os.path.join(PROJECT_DIR, "node_modules", ".bin", "tsx")
    assert os.path.isfile(tsx_bin) or os.path.islink(tsx_bin), (
        f"tsx is not installed in the project; expected executable at {tsx_bin}."
    )


def test_capacitor_config_exists():
    config_path = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    assert os.path.isfile(config_path), (
        f"capacitor.config.ts not found at {config_path}; the Capacitor project must be initialized."
    )


def test_capacitor_config_initially_lacks_http_plugin_enabled():
    """The initial config should not yet have CapacitorHttp enabled — the executor must add it."""
    config_path = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    with open(config_path) as f:
        contents = f.read()
    # The agent's job is to add `CapacitorHttp: { enabled: true }`. Make sure it isn't
    # already present, otherwise the task would be a no-op.
    normalized = "".join(contents.split())
    assert "CapacitorHttp:{enabled:true}" not in normalized, (
        "CapacitorHttp.enabled is already true in capacitor.config.ts; the initial state is wrong."
    )


def test_scripts_directory_exists():
    scripts_dir = os.path.join(PROJECT_DIR, "scripts")
    assert os.path.isdir(scripts_dir), (
        f"Expected scripts/ directory to exist at {scripts_dir} for the agent to place http-cli.ts."
    )


def test_http_cli_not_yet_created():
    """The executor must create scripts/http-cli.ts themselves."""
    cli_path = os.path.join(PROJECT_DIR, "scripts", "http-cli.ts")
    assert not os.path.exists(cli_path), (
        f"scripts/http-cli.ts already exists at {cli_path}; the task would be a no-op."
    )
