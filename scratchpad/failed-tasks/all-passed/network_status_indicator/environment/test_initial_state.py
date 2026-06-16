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


def test_vite_is_a_dependency():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps: dict[str, str] = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "vite" in deps, "Expected Vite to be installed as a (dev) dependency in package.json."


def test_capacitor_core_and_cli_are_dependencies():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps: dict[str, str] = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    for required in ("@capacitor/core", "@capacitor/cli"):
        assert required in deps, (
            f"Expected '{required}' to be declared in dependencies or devDependencies "
            f"of {pkg} as part of the pre-scaffolded Capacitor v8 setup."
        )


def test_index_html_exists():
    html = os.path.join(PROJECT_DIR, "index.html")
    assert os.path.isfile(html), f"Expected the Vite entry HTML at {html}."


def test_node_modules_installed():
    nm = os.path.join(PROJECT_DIR, "node_modules")
    assert os.path.isdir(nm), (
        f"Expected dependencies to be pre-installed at {nm}. The task starts from "
        "an already-installed Vite + Capacitor v8 project."
    )


def test_capacitor_config_present():
    # Capacitor v8 is pre-initialized; the config file must already exist so the
    # executor can focus on installing the Network plugin and wiring it up.
    candidates = [
        os.path.join(PROJECT_DIR, "capacitor.config.ts"),
        os.path.join(PROJECT_DIR, "capacitor.config.js"),
        os.path.join(PROJECT_DIR, "capacitor.config.json"),
    ]
    assert any(os.path.isfile(p) for p in candidates), (
        "Expected a pre-existing Capacitor config file (capacitor.config.ts/js/json) "
        f"in {PROJECT_DIR}."
    )


def test_network_plugin_not_yet_installed():
    # The executor is responsible for installing @capacitor/network.
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps: dict[str, str] = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "@capacitor/network" not in deps, (
        "'@capacitor/network' should NOT be declared in package.json before the task "
        "starts; installing it is part of the task."
    )
    assert not os.path.isdir(
        os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "network")
    ), (
        "node_modules/@capacitor/network should NOT exist before the task starts."
    )


def test_index_html_has_no_net_status_element():
    # The starting markup must not already contain #net-status, so the task
    # genuinely requires the executor to add it.
    html = os.path.join(PROJECT_DIR, "index.html")
    with open(html) as f:
        content = f.read()
    assert "net-status" not in content, (
        "The starting index.html should NOT contain a '#net-status' element; "
        "creating it is part of the task."
    )
