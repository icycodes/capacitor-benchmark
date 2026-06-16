import json
import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myapp"


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


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_package_json_exists():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg), f"package.json not found at {pkg}."


def test_package_json_is_valid_json():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    assert isinstance(data, dict), "package.json must contain a JSON object."
    assert "scripts" in data, "package.json must define a 'scripts' section."


def test_capacitor_core_preinstalled_in_package_json():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "@capacitor/core" in deps, (
        "Expected @capacitor/core to be declared as a (dev)dependency in package.json "
        "in the initial environment."
    )
    assert "@capacitor/cli" in deps, (
        "Expected @capacitor/cli to be declared as a (dev)dependency in package.json "
        "in the initial environment."
    )


def test_capacitor_core_module_installed():
    core_pkg = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "core", "package.json"
    )
    assert os.path.isfile(core_pkg), (
        f"Expected @capacitor/core to be pre-installed under node_modules at {core_pkg}."
    )


def test_capacitor_cli_module_installed():
    cli_pkg = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "cli", "package.json"
    )
    assert os.path.isfile(cli_pkg), (
        f"Expected @capacitor/cli to be pre-installed under node_modules at {cli_pkg}."
    )


def test_capacitor_config_present():
    found = False
    for name in ("capacitor.config.ts", "capacitor.config.js", "capacitor.config.json"):
        if os.path.isfile(os.path.join(PROJECT_DIR, name)):
            found = True
            break
    assert found, (
        f"Expected a Capacitor config file (capacitor.config.{{ts,js,json}}) to be "
        f"pre-created in {PROJECT_DIR}."
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
# Negative checks: the initial state must NOT already satisfy the task.
# ---------------------------------------------------------------------------


def test_capacitor_android_not_in_package_json():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "@capacitor/android" not in deps, (
        "@capacitor/android must NOT be declared in package.json before the task; "
        "the executor is expected to install it."
    )


def test_capacitor_ios_not_in_package_json():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "@capacitor/ios" not in deps, (
        "@capacitor/ios must NOT be declared in package.json before the task; "
        "the executor is expected to install it."
    )


def test_capacitor_android_not_in_node_modules():
    p = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "android", "package.json"
    )
    assert not os.path.exists(p), (
        f"{p} must NOT exist before the task starts; the executor must install it."
    )


def test_capacitor_ios_not_in_node_modules():
    p = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "ios", "package.json")
    assert not os.path.exists(p), (
        f"{p} must NOT exist before the task starts; the executor must install it."
    )
