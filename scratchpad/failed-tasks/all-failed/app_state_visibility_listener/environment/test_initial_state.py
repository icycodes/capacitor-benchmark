import json
import os
import re
import shutil
import subprocess

PROJECT_DIR = "/home/user/myapp"
SRC_DIR = os.path.join(PROJECT_DIR, "src")


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
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_src_directory_exists():
    assert os.path.isdir(SRC_DIR), f"Project source directory {SRC_DIR} does not exist."


def test_package_json_exists():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg), f"package.json not found at {pkg}."


def test_package_json_is_valid_json():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    assert isinstance(data, dict), "package.json must contain a JSON object."
    assert "scripts" in data, "package.json must define a 'scripts' section."


def test_capacitor_core_and_cli_pre_installed():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "@capacitor/core" in deps, (
        "Expected '@capacitor/core' to be pre-installed in package.json."
    )
    assert "@capacitor/cli" in deps, (
        "Expected '@capacitor/cli' to be pre-installed in package.json so that "
        "`npx cap sync` can run without an extra install step."
    )


def test_app_plugin_not_yet_installed():
    """The @capacitor/app plugin must NOT already appear in package.json."""
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "@capacitor/app" not in deps, (
        "Expected '@capacitor/app' to NOT be pre-installed; the executor must "
        "add it to satisfy the task."
    )


def test_app_plugin_node_modules_absent():
    """node_modules must not yet contain @capacitor/app."""
    plugin_dir = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "app"
    )
    assert not os.path.isdir(plugin_dir), (
        f"Expected {plugin_dir} to be absent before the task starts."
    )


def test_node_modules_installed():
    nm = os.path.join(PROJECT_DIR, "node_modules")
    assert os.path.isdir(nm), (
        f"Expected dependencies to be pre-installed at {nm}. The task starts from an "
        "already-installed Vite + Capacitor project."
    )


def test_vite_installed():
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


def test_index_html_does_not_contain_app_state_element():
    """The pre-scaffolded index.html must NOT already contain #app-state."""
    html = os.path.join(PROJECT_DIR, "index.html")
    with open(html) as f:
        content = f.read()
    pattern = re.compile(r"""id\s*=\s*["']app-state["']""")
    assert not pattern.search(content), (
        f"The initial {html} must not already contain an element with id='app-state'."
    )


def test_main_ts_exists():
    main_ts = os.path.join(SRC_DIR, "main.ts")
    assert os.path.isfile(main_ts), (
        f"Expected the TypeScript entry module at {main_ts}."
    )


def test_capacitor_config_present():
    ts_path = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    json_path = os.path.join(PROJECT_DIR, "capacitor.config.json")
    assert os.path.isfile(ts_path) or os.path.isfile(json_path), (
        "Expected a Capacitor config (capacitor.config.ts or .json) to be present at "
        f"{PROJECT_DIR} before the task starts."
    )


def test_initial_sources_do_not_import_capacitor_app():
    """No file under src/ should already import from @capacitor/app."""
    pattern = re.compile(r"@capacitor/app")
    for root, _, files in os.walk(SRC_DIR):
        for name in files:
            if not name.endswith((".ts", ".tsx", ".js", ".mjs")):
                continue
            path = os.path.join(root, name)
            with open(path) as f:
                content = f.read()
            assert not pattern.search(content), (
                f"The initial source {path} must not already import "
                "from '@capacitor/app'."
            )


def test_initial_sources_do_not_call_app_state_change_listener():
    """No source file should already register an appStateChange listener."""
    pattern = re.compile(r"appStateChange")
    for root, _, files in os.walk(SRC_DIR):
        for name in files:
            if not name.endswith((".ts", ".tsx", ".js", ".mjs")):
                continue
            path = os.path.join(root, name)
            with open(path) as f:
                content = f.read()
            assert not pattern.search(content), (
                f"The initial source {path} must not already reference "
                "'appStateChange'."
            )


def test_initial_dist_absent():
    """The dist/ build output must not yet exist before the executor runs the task."""
    dist_index = os.path.join(PROJECT_DIR, "dist", "index.html")
    assert not os.path.isfile(dist_index), (
        f"Expected {dist_index} to be absent in the initial state; the executor must "
        "produce it via `npm run build`."
    )


def test_playwright_chromium_installed_for_verifier():
    """Playwright Python and a bundled Chromium must be ready for the verifier."""
    import importlib.util

    spec = importlib.util.find_spec("playwright")
    assert spec is not None, (
        "Expected the 'playwright' Python package to be installed for the verifier."
    )
    # Confirm that the playwright CLI is available so chromium can be launched.
    assert shutil.which("playwright") is not None, (
        "Expected the 'playwright' CLI to be available in PATH for headless "
        "Chromium verification."
    )
