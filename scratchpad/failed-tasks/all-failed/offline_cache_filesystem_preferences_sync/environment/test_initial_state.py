import json
import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myapp"
FIXTURE_SERVER = "/opt/fixtures/etag_server.js"


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
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "vite" in deps, (
        "Expected Vite to be installed as a (dev) dependency in package.json."
    )


def test_index_html_exists():
    html = os.path.join(PROJECT_DIR, "index.html")
    assert os.path.isfile(html), f"Expected the Vite entry HTML at {html}."


def test_node_modules_installed():
    nm = os.path.join(PROJECT_DIR, "node_modules")
    assert os.path.isdir(nm), (
        f"Expected dependencies to be pre-installed at {nm}. The task starts from "
        "an already-installed Vite project."
    )


def test_capacitor_not_yet_initialized():
    # The executor is expected to initialize Capacitor; ensure the config file
    # is not already present in the starting environment.
    for name in (
        "capacitor.config.ts",
        "capacitor.config.js",
        "capacitor.config.json",
    ):
        path = os.path.join(PROJECT_DIR, name)
        assert not os.path.exists(path), (
            f"Capacitor config {path} should not exist before the task starts."
        )


def test_offline_cache_module_not_yet_present():
    module_path = os.path.join(PROJECT_DIR, "src", "cache", "offlineCache.ts")
    assert not os.path.exists(module_path), (
        f"The offline cache module {module_path} should be created by the executor; "
        "it must not already exist."
    )


def test_fixture_server_script_exists():
    assert os.path.isfile(FIXTURE_SERVER), (
        f"Expected the ETag-aware fixture server script at {FIXTURE_SERVER}. "
        "The verifier relies on it to drive ETag/If-None-Match behaviour."
    )


def test_fixture_server_script_is_node_module():
    with open(FIXTURE_SERVER) as f:
        head = f.read(2048)
    # The bundled fixture is a Node.js script; it must at minimum require the http module.
    assert "require(" in head or "import " in head, (
        f"Fixture server at {FIXTURE_SERVER} does not look like a Node.js script."
    )
