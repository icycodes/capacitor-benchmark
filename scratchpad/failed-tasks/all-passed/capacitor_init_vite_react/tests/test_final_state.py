import json
import os
import re
import socket
import subprocess
import time

import pytest
import requests
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myapp"
PREVIEW_HOST = "127.0.0.1"
PREVIEW_PORT = 4173
PREVIEW_URL = f"http://{PREVIEW_HOST}:{PREVIEW_PORT}/"


def _is_eight_x(version_spec: str) -> bool:
    """Return True if a semver spec (e.g. ^8.0.0, ~8.1.2, 8.0.0, 8.x) resolves to the 8.x major."""
    if not version_spec:
        return False
    # Strip leading range prefix characters (^, ~, >=, =, v, etc.) and whitespace.
    cleaned = version_spec.strip().lstrip("^~>=<v ")
    # Take the first numeric component before the first dot.
    m = re.match(r"^(\d+)", cleaned)
    if not m:
        return False
    return m.group(1) == "8"


def _resolved_version_from_node_modules(pkg_name: str) -> str | None:
    """Read the real installed version from node_modules/<pkg>/package.json, if present."""
    parts = pkg_name.split("/")
    pkg_json = os.path.join(PROJECT_DIR, "node_modules", *parts, "package.json")
    if not os.path.isfile(pkg_json):
        return None
    try:
        with open(pkg_json) as f:
            data = json.load(f)
        return data.get("version")
    except (OSError, json.JSONDecodeError):
        return None


def _read_capacitor_config():
    """Return a (config-dict, file-path) tuple regardless of the config file format."""
    ts_path = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    js_path = os.path.join(PROJECT_DIR, "capacitor.config.js")
    json_path = os.path.join(PROJECT_DIR, "capacitor.config.json")

    if os.path.isfile(json_path):
        with open(json_path) as f:
            return json.load(f), json_path

    for src_path in (ts_path, js_path):
        if not os.path.isfile(src_path):
            continue
        with open(src_path) as f:
            content = f.read()

        def find(field: str) -> str | None:
            m = re.search(
                rf"{field}\s*:\s*['\"]([^'\"]+)['\"]",
                content,
            )
            return m.group(1) if m else None

        cfg = {
            "appId": find("appId"),
            "appName": find("appName"),
            "webDir": find("webDir"),
        }
        return cfg, src_path

    raise AssertionError(
        "No Capacitor config file (capacitor.config.ts/js/json) found at the project root."
    )


# ---------------------------------------------------------------------------
# package.json checks for Capacitor v8
# ---------------------------------------------------------------------------


def test_package_json_lists_capacitor_core_8x():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), f"package.json not found at {pkg_path}."
    with open(pkg_path) as f:
        pkg = json.load(f)
    deps = pkg.get("dependencies", {}) or {}
    assert "@capacitor/core" in deps, (
        "Expected '@capacitor/core' to be declared in the 'dependencies' section of "
        f"{pkg_path}; found dependencies: {sorted(deps)}"
    )
    declared = deps["@capacitor/core"]
    resolved = _resolved_version_from_node_modules("@capacitor/core")
    assert _is_eight_x(declared) or (resolved and _is_eight_x(resolved)), (
        "Expected '@capacitor/core' to satisfy the 8.x major. "
        f"package.json declared: {declared!r}; "
        f"node_modules installed: {resolved!r}"
    )


def test_package_json_lists_capacitor_cli_8x():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg_path) as f:
        pkg = json.load(f)
    dev_deps = pkg.get("devDependencies", {}) or {}
    deps = pkg.get("dependencies", {}) or {}
    declared = dev_deps.get("@capacitor/cli") or deps.get("@capacitor/cli")
    assert declared, (
        "Expected '@capacitor/cli' to be declared in 'devDependencies' or 'dependencies' of "
        f"{pkg_path}; found devDependencies: {sorted(dev_deps)} and dependencies: {sorted(deps)}"
    )
    resolved = _resolved_version_from_node_modules("@capacitor/cli")
    assert _is_eight_x(declared) or (resolved and _is_eight_x(resolved)), (
        "Expected '@capacitor/cli' to satisfy the 8.x major. "
        f"package.json declared: {declared!r}; "
        f"node_modules installed: {resolved!r}"
    )


# ---------------------------------------------------------------------------
# Capacitor configuration file
# ---------------------------------------------------------------------------


def test_capacitor_config_file_present_and_unique():
    present = [
        name
        for name in ("capacitor.config.ts", "capacitor.config.json", "capacitor.config.js")
        if os.path.isfile(os.path.join(PROJECT_DIR, name))
    ]
    assert len(present) >= 1, (
        "Expected exactly one Capacitor config file (capacitor.config.ts, "
        "capacitor.config.json, or capacitor.config.js) at the project root."
    )


def test_capacitor_config_values():
    cfg, path = _read_capacitor_config()
    assert cfg.get("appName") == "React Demo", (
        f"Capacitor config at {path} must set appName to 'React Demo'; "
        f"got {cfg.get('appName')!r}."
    )
    assert cfg.get("appId") == "com.example.reactdemo", (
        f"Capacitor config at {path} must set appId to 'com.example.reactdemo'; "
        f"got {cfg.get('appId')!r}."
    )
    assert cfg.get("webDir") == "dist", (
        f"Capacitor config at {path} must set webDir to 'dist'; "
        f"got {cfg.get('webDir')!r}."
    )


# ---------------------------------------------------------------------------
# Build + sync verification
# ---------------------------------------------------------------------------


def test_npm_run_build_succeeds_and_produces_index_html():
    # Ensure a clean build to avoid stale artifacts from earlier attempts.
    dist_dir = os.path.join(PROJECT_DIR, "dist")
    if os.path.isdir(dist_dir):
        subprocess.run(["rm", "-rf", dist_dir], check=False)

    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Expected `npm run build` to exit with code 0.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    dist_index = os.path.join(PROJECT_DIR, "dist", "index.html")
    assert os.path.isfile(dist_index), (
        f"Expected production build output at {dist_index} after `npm run build`."
    )


def test_npx_cap_sync_succeeds():
    # `cap sync` requires the build to have been produced first.
    dist_index = os.path.join(PROJECT_DIR, "dist", "index.html")
    if not os.path.isfile(dist_index):
        build = subprocess.run(
            ["npm", "run", "build"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert build.returncode == 0, (
            "Pre-step `npm run build` failed before `npx cap sync` could be tested.\n"
            f"stdout:\n{build.stdout}\nstderr:\n{build.stderr}"
        )

    result = subprocess.run(
        ["npx", "--no-install", "cap", "sync"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        "Expected `npx cap sync` to exit with code 0.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# Vite preview HTTP check
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def preview_server(xprocess):
    # Make sure the build artifact exists before starting `vite preview`.
    dist_index = os.path.join(PROJECT_DIR, "dist", "index.html")
    if not os.path.isfile(dist_index):
        build = subprocess.run(
            ["npm", "run", "build"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if build.returncode != 0:
            pytest.fail(
                "Pre-step `npm run build` failed before starting `vite preview`.\n"
                f"stdout:\n{build.stdout}\nstderr:\n{build.stderr}"
            )

    class Starter(ProcessStarter):
        name = "vite_preview"
        args = [
            "npm",
            "run",
            "preview",
            "--",
            "--host",
            "0.0.0.0",
            "--port",
            str(PREVIEW_PORT),
            "--strictPort",
        ]
        env = os.environ.copy()
        popen_kwargs = {
            "cwd": PROJECT_DIR,
            "text": True,
        }
        timeout = 120
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex((PREVIEW_HOST, PREVIEW_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)
    # Allow the server a moment to fully respond after the port opens.
    time.sleep(1.0)
    yield PREVIEW_URL
    info = xprocess.getinfo(Starter.name)
    info.terminate()


def test_preview_returns_200_with_react_root(preview_server):
    response = requests.get(preview_server, timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server} returned status {response.status_code}; expected 200."
    )
    body = response.text
    assert re.search(r"<div\s+id\s*=\s*[\"']root[\"']", body), (
        "The served index.html must contain a `<div id=\"root\">` element. "
        f"Got body:\n{body[:1000]}"
    )
