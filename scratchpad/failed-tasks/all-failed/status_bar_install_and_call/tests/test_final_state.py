import json
import os
import re
import shutil
import socket
import subprocess
from urllib.parse import urljoin

import pytest
import requests
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myapp"
SRC_DIR = os.path.join(PROJECT_DIR, "src")

PREVIEW_HOST = "127.0.0.1"
PREVIEW_PORT = 4173
PREVIEW_URL = f"http://{PREVIEW_HOST}:{PREVIEW_PORT}/"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


SOURCE_EXTENSIONS = (".ts", ".tsx", ".js", ".mjs")


def _iter_source_files():
    for root, _, files in os.walk(SRC_DIR):
        for name in files:
            if name.endswith(SOURCE_EXTENSIONS):
                yield os.path.join(root, name)


def _read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _semver_major(version_str):
    """Return the integer semver major component for an arbitrary spec."""
    if not isinstance(version_str, str):
        return None
    cleaned = version_str.strip().lstrip("^~=>< vV")
    match = re.match(r"(\d+)", cleaned)
    return int(match.group(1)) if match else None


# ---------------------------------------------------------------------------
# Truth Step 1: package.json declares @capacitor/status-bar at major 8
# ---------------------------------------------------------------------------


def test_status_bar_dependency_at_major_8():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), (
        f"Expected package.json at {pkg_path} after the task completes."
    )
    with open(pkg_path) as f:
        data = json.load(f)
    deps = data.get("dependencies") or {}
    assert isinstance(deps, dict), "package.json 'dependencies' must be an object."
    assert "@capacitor/status-bar" in deps, (
        "Expected '@capacitor/status-bar' to be declared in package.json "
        "'dependencies' after the task completes; got dependencies="
        f"{sorted(deps.keys())}."
    )

    # Prefer the installed version from node_modules when available, otherwise
    # fall back to the specifier string in package.json itself.
    installed_pkg_path = os.path.join(
        PROJECT_DIR,
        "node_modules",
        "@capacitor",
        "status-bar",
        "package.json",
    )
    resolved_major = None
    if os.path.isfile(installed_pkg_path):
        with open(installed_pkg_path) as f:
            installed = json.load(f)
        installed_version = installed.get("version")
        resolved_major = _semver_major(installed_version)
        assert resolved_major == 8, (
            "Expected the installed '@capacitor/status-bar' to be at major version 8, "
            f"but {installed_pkg_path} reports version={installed_version!r}."
        )
    else:
        spec_major = _semver_major(deps["@capacitor/status-bar"])
        assert spec_major == 8, (
            "Expected package.json to pin '@capacitor/status-bar' to a v8 specifier; "
            f"got {deps['@capacitor/status-bar']!r}."
        )


# ---------------------------------------------------------------------------
# Truth Step 2: a TS source file imports StatusBar+Style and contains both calls
# ---------------------------------------------------------------------------


IMPORT_PATTERN = re.compile(
    # Match: import { StatusBar, Style } from '@capacitor/status-bar'
    # or:    import { Style , StatusBar } from "@capacitor/status-bar";
    r"import\s*\{[^}]*\}\s*from\s*['\"]@capacitor/status-bar['\"]",
    re.DOTALL,
)

SET_STYLE_PATTERN = re.compile(
    r"StatusBar\s*\.\s*setStyle\s*\(\s*\{\s*style\s*:\s*Style\s*\.\s*Dark\s*\}\s*\)",
    re.DOTALL,
)

SET_BG_PATTERN = re.compile(
    r"StatusBar\s*\.\s*setBackgroundColor\s*\(\s*\{\s*color\s*:\s*['\"]#222222['\"]\s*\}\s*\)",
    re.DOTALL,
)


def _has_status_bar_and_style_import(content):
    for match in IMPORT_PATTERN.finditer(content):
        block = match.group(0)
        if "StatusBar" in block and "Style" in block:
            return True
    return False


def test_source_imports_status_bar_and_style():
    matching_files = [
        path for path in _iter_source_files() if _has_status_bar_and_style_import(_read(path))
    ]
    assert matching_files, (
        "Expected at least one source file under "
        f"{SRC_DIR} to contain an `import {{ StatusBar, Style }} from "
        "'@capacitor/status-bar'` statement (members in any order)."
    )


def test_source_calls_set_style_with_dark():
    matching_files = [
        path for path in _iter_source_files() if SET_STYLE_PATTERN.search(_read(path))
    ]
    assert matching_files, (
        "Expected at least one source file under "
        f"{SRC_DIR} to contain a call matching "
        "`StatusBar.setStyle({ style: Style.Dark })`."
    )


def test_source_calls_set_background_color_222222():
    matching_files = [
        path for path in _iter_source_files() if SET_BG_PATTERN.search(_read(path))
    ]
    assert matching_files, (
        "Expected at least one source file under "
        f"{SRC_DIR} to contain a call matching "
        "`StatusBar.setBackgroundColor({ color: '#222222' })` (single or "
        "double quotes accepted)."
    )


# ---------------------------------------------------------------------------
# Truth Steps 3 & 4: production build + cap sync
# ---------------------------------------------------------------------------


def test_npm_build_succeeds_and_dist_index_exists():
    dist_dir = os.path.join(PROJECT_DIR, "dist")
    if os.path.isdir(dist_dir):
        shutil.rmtree(dist_dir)

    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, (
        "Expected `npm run build` to exit with code 0.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )

    dist_index = os.path.join(dist_dir, "index.html")
    assert os.path.isfile(dist_index), (
        f"Expected production build artifact at {dist_index} after `npm run build`."
    )


def test_cap_sync_succeeds():
    result = subprocess.run(
        ["npx", "--no-install", "cap", "sync"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Expected `npx cap sync` to exit with code 0.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# Truth Step 5: preview HTTP 200 + bundle contains setStyle...Dark
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def preview_server(xprocess):
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
    yield PREVIEW_URL
    info = xprocess.getinfo(Starter.name)
    info.terminate()


SCRIPT_SRC_PATTERN = re.compile(
    r"<script\b[^>]*\bsrc\s*=\s*[\"']([^\"']+\.js)[\"'][^>]*>",
    re.IGNORECASE,
)


def test_preview_serves_html_and_bundle_contains_setstyle_dark(preview_server):
    response = requests.get(preview_server, timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server} returned status {response.status_code}; expected 200."
    )

    html_body = response.text
    script_srcs = SCRIPT_SRC_PATTERN.findall(html_body)
    assert script_srcs, (
        "Expected the served index.html to reference at least one <script src=...> "
        f"pointing to a .js bundle. Body was:\n{html_body[:1500]}"
    )

    # Walk every referenced JS asset and collect their concatenated contents.
    # We pass if any bundle (directly referenced or transitively imported) matches
    # the setStyle...Dark regex, mirroring how the executor's call survives Vite's
    # bundler.
    bundle_pattern = re.compile(r"setStyle[\s\S]*?Dark")

    visited = set()
    to_visit = list(script_srcs)
    import_pattern = re.compile(r"""import\s*\(?\s*["']([^"']+\.js)["']""")
    bare_import_pattern = re.compile(r"""from\s*["']([^"']+\.js)["']""")
    all_bodies = []

    while to_visit:
        src = to_visit.pop()
        if src in visited:
            continue
        visited.add(src)
        bundle_url = urljoin(preview_server, src)
        try:
            bundle_resp = requests.get(bundle_url, timeout=30)
        except requests.RequestException as exc:
            pytest.fail(f"Failed to fetch JS bundle at {bundle_url}: {exc}")
        assert bundle_resp.status_code == 200, (
            f"GET {bundle_url} returned status {bundle_resp.status_code}; expected 200."
        )
        body = bundle_resp.text
        all_bodies.append((bundle_url, body))
        if bundle_pattern.search(body):
            return  # Pass: bundle contains the required substring.

        # Follow any nested .js imports referenced from the bundle so we can
        # locate the actual chunk that contains the StatusBar.setStyle call.
        for candidate in import_pattern.findall(body) + bare_import_pattern.findall(body):
            if candidate not in visited:
                to_visit.append(candidate)

    snippets = "\n".join(
        f"-- {url} --\n{body[:400]}" for url, body in all_bodies
    )
    pytest.fail(
        "Expected one of the served JS bundles to contain a substring matching the "
        "regex `setStyle.*Dark`, proving that `StatusBar.setStyle({ style: Style.Dark })` "
        "survived bundling. None matched.\n"
        f"Scanned bundle URLs: {sorted(visited)}\n"
        f"First 400 bytes of each:\n{snippets}"
    )
