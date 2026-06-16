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
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "vite" in deps, "Expected Vite to be installed as a (dev) dependency in package.json."


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
    # The executor must initialize Capacitor; ensure no config file is present
    # at the starting environment.
    for name in ("capacitor.config.ts", "capacitor.config.js", "capacitor.config.json"):
        path = os.path.join(PROJECT_DIR, name)
        assert not os.path.exists(path), (
            f"Capacitor config {path} should not exist before the task starts."
        )


def test_capacitor_device_not_yet_installed():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "@capacitor/device" not in deps, (
        "The @capacitor/device plugin should not be declared in package.json before "
        "the task starts; the executor is expected to install it."
    )
    assert "@capacitor/core" not in deps, (
        "The @capacitor/core package should not be declared in package.json before "
        "the task starts; the executor is expected to install it."
    )


def test_initial_markup_has_no_device_elements():
    html = os.path.join(PROJECT_DIR, "index.html")
    with open(html) as f:
        body = f.read()
    for marker in ("device-platform", "device-os-version", "device-lang", "lang-btn"):
        assert marker not in body, (
            f"The starting index.html unexpectedly already references '{marker}'."
        )


def test_initial_main_script_has_no_device_api_usage():
    main_ts = os.path.join(PROJECT_DIR, "src", "main.ts")
    assert os.path.isfile(main_ts), f"Expected the entry script at {main_ts}."
    with open(main_ts) as f:
        body = f.read()
    assert "@capacitor/device" not in body, (
        "The starting src/main.ts should not import @capacitor/device."
    )
