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


def test_capacitor_core_is_a_dependency_at_major_8():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "@capacitor/core" in deps, (
        "Expected '@capacitor/core' to be pre-installed as a dependency in package.json."
    )
    assert "@capacitor/cli" in deps, (
        "Expected '@capacitor/cli' to be pre-installed as a dependency in package.json."
    )
    core_pkg = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "core", "package.json")
    assert os.path.isfile(core_pkg), (
        f"Expected @capacitor/core to be installed at {core_pkg}."
    )
    with open(core_pkg) as f:
        core_data = json.load(f)
    version = str(core_data.get("version", ""))
    major = version.split(".")[0]
    assert major == "8", (
        f"Expected installed @capacitor/core to be version 8.x; found {version!r}."
    )


def test_filesystem_plugin_not_installed_yet():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "@capacitor/filesystem" not in deps, (
        "'@capacitor/filesystem' should NOT be listed in package.json before the task starts; "
        "installing it is part of the task."
    )
    installed = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "filesystem"
    )
    assert not os.path.isdir(installed), (
        f"@capacitor/filesystem should not be pre-installed at {installed}."
    )


def test_index_html_exists():
    html = os.path.join(PROJECT_DIR, "index.html")
    assert os.path.isfile(html), f"Expected the Vite entry HTML at {html}."


def test_index_html_does_not_have_required_elements():
    html = os.path.join(PROJECT_DIR, "index.html")
    with open(html) as f:
        body = f.read()
    for required_id in ("write-btn", "read-btn", "file-content"):
        assert not re.search(rf"id\s*=\s*[\"']{re.escape(required_id)}[\"']", body), (
            f"The starting index.html must NOT already contain an element with "
            f'id="{required_id}"; wiring it up is part of the task.'
        )


def test_node_modules_installed():
    nm = os.path.join(PROJECT_DIR, "node_modules")
    assert os.path.isdir(nm), (
        f"Expected dependencies to be pre-installed at {nm}. The task starts from "
        "an already-installed Vite + Capacitor project."
    )


def test_capacitor_config_present():
    # The Capacitor config is pre-scaffolded so that the executor only needs to
    # add the Filesystem plugin and the UI. At least one of the standard config
    # file shapes must exist.
    candidates = [
        os.path.join(PROJECT_DIR, "capacitor.config.ts"),
        os.path.join(PROJECT_DIR, "capacitor.config.js"),
        os.path.join(PROJECT_DIR, "capacitor.config.json"),
    ]
    assert any(os.path.isfile(p) for p in candidates), (
        "Expected a pre-existing capacitor.config.{ts,js,json} at the project root."
    )


def test_no_prior_build_output():
    dist = os.path.join(PROJECT_DIR, "dist")
    assert not os.path.isdir(dist), (
        f"Expected no pre-existing build output at {dist}; the executor must run "
        "`npm run build` as part of the task."
    )
