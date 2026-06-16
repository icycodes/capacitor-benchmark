import json
import os
import re
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
    assert os.path.isdir(PROJECT_DIR), (
        f"Pre-scaffolded project directory {PROJECT_DIR} does not exist."
    )


def test_package_json_exists_and_is_valid_json():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg), f"package.json not found at {pkg}."
    with open(pkg) as f:
        data = json.load(f)
    assert isinstance(data, dict), "package.json must contain a JSON object."
    assert "scripts" in data, "package.json must define a 'scripts' section."


def test_vite_is_a_dependency():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "vite" in deps, (
        "Expected Vite to be installed as a (dev) dependency in package.json."
    )


def test_index_html_exists():
    html = os.path.join(PROJECT_DIR, "index.html")
    assert os.path.isfile(html), f"Expected the Vite entry HTML at {html}."


def test_main_ts_exists():
    main_ts = os.path.join(PROJECT_DIR, "src", "main.ts")
    assert os.path.isfile(main_ts), (
        f"Expected the Vite entry script at {main_ts}; the executor will extend it."
    )


def test_node_modules_installed():
    nm = os.path.join(PROJECT_DIR, "node_modules")
    assert os.path.isdir(nm), (
        f"Expected dependencies to be pre-installed at {nm}. The task starts from "
        "an already-installed Vite + Capacitor v8 base project."
    )


def test_capacitor_already_initialised():
    cfg = None
    for name in ("capacitor.config.ts", "capacitor.config.js", "capacitor.config.json"):
        candidate = os.path.join(PROJECT_DIR, name)
        if os.path.isfile(candidate):
            cfg = candidate
            break
    assert cfg is not None, (
        "Expected a pre-existing Capacitor config file (capacitor.config.ts/js/json) "
        f"at the root of {PROJECT_DIR}."
    )
    with open(cfg) as f:
        content = f.read()
    assert "com.example.tracker" in content, (
        f"Expected the pre-existing Capacitor config {cfg} to set appId 'com.example.tracker'."
    )
    assert "Tracker App" in content, (
        f"Expected the pre-existing Capacitor config {cfg} to set appName 'Tracker App'."
    )
    # webDir must be 'dist' to align with Vite's default output.
    assert re.search(r"webDir\s*[:=]\s*['\"]dist['\"]", content) or '"webDir": "dist"' in content, (
        f"Expected the pre-existing Capacitor config {cfg} to set webDir to 'dist'."
    )


def test_capacitor_core_and_cli_preinstalled():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "@capacitor/core" in deps, (
        "Expected @capacitor/core to be pre-installed in package.json."
    )
    assert "@capacitor/cli" in deps, (
        "Expected @capacitor/cli to be pre-installed in package.json."
    )


def test_target_plugins_not_yet_installed():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    for plugin in ("@capacitor/app", "@capacitor/geolocation", "@capacitor/preferences"):
        assert plugin not in deps, (
            f"Plugin '{plugin}' should NOT yet be declared in package.json before the task starts."
        )
        installed_dir = os.path.join(
            PROJECT_DIR, "node_modules", "@capacitor", plugin.split("/")[1]
        )
        assert not os.path.isdir(installed_dir), (
            f"Plugin '{plugin}' should NOT yet be installed at {installed_dir} before the task starts."
        )


def test_tracker_not_yet_exposed_in_main_ts():
    main_ts = os.path.join(PROJECT_DIR, "src", "main.ts")
    with open(main_ts) as f:
        content = f.read()
    assert "window.tracker" not in content and "(window as any).tracker" not in content, (
        f"The pre-scaffolded {main_ts} should NOT yet expose a global tracker; "
        "the executor is responsible for wiring it up."
    )
