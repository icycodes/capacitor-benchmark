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


def test_capacitor_core_installed():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "@capacitor/core" in deps, (
        "Expected '@capacitor/core' to be pre-installed; the executor only enables the "
        "CapacitorHttp plugin (which is bundled with @capacitor/core)."
    )
    assert "@capacitor/cli" in deps, (
        "Expected '@capacitor/cli' to be pre-installed so that `npx cap sync` can run."
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
    assert "vite" in deps, "Expected Vite to be installed as a (dev) dependency in package.json."


def test_index_html_exists():
    html = os.path.join(PROJECT_DIR, "index.html")
    assert os.path.isfile(html), f"Expected the Vite entry HTML at {html}."


def test_capacitor_config_present():
    ts_path = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    json_path = os.path.join(PROJECT_DIR, "capacitor.config.json")
    assert os.path.isfile(ts_path) or os.path.isfile(json_path), (
        "Expected a Capacitor config (capacitor.config.ts or .json) to be present at "
        f"{PROJECT_DIR} before the task starts."
    )


def test_capacitor_http_not_yet_enabled():
    """The plugin must NOT already be enabled in the initial environment."""
    ts_path = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    json_path = os.path.join(PROJECT_DIR, "capacitor.config.json")

    if os.path.isfile(json_path):
        with open(json_path) as f:
            cfg = json.load(f)
        plugins = (cfg.get("plugins") or {}) if isinstance(cfg, dict) else {}
        cap_http = (plugins.get("CapacitorHttp") or {}) if isinstance(plugins, dict) else {}
        enabled = cap_http.get("enabled") if isinstance(cap_http, dict) else None
        assert enabled is not True, (
            f"capacitor.config.json must NOT already enable CapacitorHttp; got "
            f"plugins.CapacitorHttp.enabled={enabled!r}."
        )

    if os.path.isfile(ts_path):
        with open(ts_path) as f:
            content = f.read()
        # Look for a CapacitorHttp block that turns enabled: true.
        pattern = re.compile(
            r"CapacitorHttp\s*:\s*\{[^}]*enabled\s*:\s*true",
            re.DOTALL,
        )
        assert not pattern.search(content), (
            "capacitor.config.ts must NOT already enable CapacitorHttp; found a "
            "'CapacitorHttp: { ... enabled: true ... }' block."
        )


def test_initial_html_has_no_fetch_button():
    """The initial scaffold must NOT already satisfy the final-state UI criteria."""
    html_path = os.path.join(PROJECT_DIR, "index.html")
    with open(html_path) as f:
        content = f.read()
    assert not re.search(r"id\s*=\s*[\"']fetch-btn[\"']", content), (
        "The initial index.html must not already contain a #fetch-btn element."
    )
    assert not re.search(r"id\s*=\s*[\"']http-status[\"']", content), (
        "The initial index.html must not already contain a #http-status element."
    )
