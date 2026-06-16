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


def _read_capacitor_config():
    """Return a dict-like view of the Capacitor config regardless of file format."""
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
# Static / config-level verification
# ---------------------------------------------------------------------------


def test_capacitor_config_values():
    cfg, path = _read_capacitor_config()
    assert cfg.get("appName") == "KV Admin", (
        f"capacitor config at {path} must set appName to 'KV Admin'; got {cfg.get('appName')!r}."
    )
    assert cfg.get("appId") == "com.example.kvadmin", (
        f"capacitor config at {path} must set appId to 'com.example.kvadmin'; "
        f"got {cfg.get('appId')!r}."
    )
    assert cfg.get("webDir") == "dist", (
        f"capacitor config at {path} must set webDir to 'dist'; got {cfg.get('webDir')!r}."
    )


def test_package_json_lists_capacitor_dependencies():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), f"package.json not found at {pkg_path}."
    with open(pkg_path) as f:
        pkg = json.load(f)
    deps: dict[str, str] = {}
    deps.update(pkg.get("dependencies", {}) or {})
    deps.update(pkg.get("devDependencies", {}) or {})
    for required in ("@capacitor/core", "@capacitor/cli", "@capacitor/preferences"):
        assert required in deps, (
            f"Expected '{required}' to be declared in dependencies or devDependencies of "
            f"{pkg_path}. Found keys: {sorted(deps)}"
        )


def test_preferences_plugin_major_version_is_8():
    pref_pkg = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "preferences", "package.json"
    )
    assert os.path.isfile(pref_pkg), (
        f"Expected the installed @capacitor/preferences package at {pref_pkg}; "
        "make sure `npm install @capacitor/preferences` was executed."
    )
    with open(pref_pkg) as f:
        data = json.load(f)
    version = str(data.get("version", ""))
    m = re.match(r"^(\d+)\.", version)
    assert m, f"Could not parse @capacitor/preferences version from {pref_pkg}; got {version!r}."
    major = int(m.group(1))
    assert major == 8, (
        f"Expected @capacitor/preferences major version 8; got {version!r}."
    )


def test_dist_index_html_exists():
    dist_index = os.path.join(PROJECT_DIR, "dist", "index.html")
    assert os.path.isfile(dist_index), (
        f"Expected production build output at {dist_index}. "
        "Make sure `npm run build` succeeded."
    )


def test_npm_build_succeeds():
    # Build is idempotent; re-running confirms the project still builds cleanly.
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Expected `npm run build` to exit 0.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    dist_index = os.path.join(PROJECT_DIR, "dist", "index.html")
    assert os.path.isfile(dist_index), (
        f"Expected `npm run build` to produce {dist_index}."
    )


def test_capacitor_sync_succeeds():
    result = subprocess.run(
        ["npx", "--no-install", "cap", "sync"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        "Expected `npx cap sync` to succeed after the production build.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# Live preview server fixture
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
    time.sleep(1.0)
    yield PREVIEW_URL
    info = xprocess.getinfo(Starter.name)
    info.terminate()


def test_index_served_with_kv_admin_markup(preview_server):
    response = requests.get(preview_server, timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server} returned status {response.status_code}; expected 200."
    )
    body = response.text
    for marker_id in ("kv-key", "kv-value", "kv-set-btn", "kv-remove-btn", "kv-clear-btn", "kv-list"):
        assert re.search(rf"id\s*=\s*[\"']{re.escape(marker_id)}[\"']", body), (
            f"The served index.html must contain an element with id=\"{marker_id}\". "
            f"Got body:\n{body[:1500]}"
        )


# ---------------------------------------------------------------------------
# Browser-driven behavioural verification
# ---------------------------------------------------------------------------


def _list_texts(page):
    return page.evaluate(
        "Array.from(document.querySelectorAll('#kv-list > li')).map(li => li.textContent)"
    )


def _list_count(page) -> int:
    return page.evaluate("document.querySelectorAll('#kv-list > li').length")


def _localstorage(page, key: str):
    return page.evaluate(
        f"window.localStorage.getItem('CapacitorStorage.{key}')"
    )


def _wait_list_count(page, expected: int, timeout_ms: int = 5000):
    page.wait_for_function(
        f"document.querySelectorAll('#kv-list > li').length === {expected}",
        timeout=timeout_ms,
    )


def test_kv_admin_multi_key_crud_flow(preview_server):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            # Fresh context => empty localStorage by default.
            context = browser.new_context()
            page = context.new_page()
            page.goto(preview_server, wait_until="load")
            page.wait_for_selector("#kv-list", state="attached", timeout=10_000)
            page.wait_for_selector("#kv-set-btn", state="visible", timeout=10_000)
            page.wait_for_timeout(300)

            # Initial state: zero entries.
            assert _list_count(page) == 0, (
                "On first load with no stored preferences, #kv-list must have zero "
                f"<li> children; got {_list_count(page)}."
            )

            # Set alpha=one.
            page.fill("#kv-key", "alpha")
            page.fill("#kv-value", "one")
            page.click("#kv-set-btn")
            _wait_list_count(page, 1)

            # Set beta=two.
            page.fill("#kv-key", "beta")
            page.fill("#kv-value", "two")
            page.click("#kv-set-btn")
            _wait_list_count(page, 2)

            texts_sorted = sorted(_list_texts(page))
            assert texts_sorted == ["alpha=one", "beta=two"], (
                "After setting alpha=one and beta=two, #kv-list must contain exactly the "
                f"items ['alpha=one', 'beta=two'] (sorted); got {texts_sorted!r}."
            )

            assert _localstorage(page, "alpha") == "one", (
                "Expected CapacitorStorage.alpha to equal 'one' in localStorage after Set; "
                f"got {_localstorage(page, 'alpha')!r}."
            )
            assert _localstorage(page, "beta") == "two", (
                "Expected CapacitorStorage.beta to equal 'two' in localStorage after Set; "
                f"got {_localstorage(page, 'beta')!r}."
            )

            # Reload — persistence check.
            page.reload(wait_until="load")
            page.wait_for_selector("#kv-list", state="attached", timeout=10_000)
            _wait_list_count(page, 2, timeout_ms=10_000)
            texts_sorted = sorted(_list_texts(page))
            assert texts_sorted == ["alpha=one", "beta=two"], (
                "After reloading the page, #kv-list must still contain ['alpha=one', "
                f"'beta=two'] (sorted); got {texts_sorted!r}."
            )

            # Remove alpha.
            page.fill("#kv-key", "alpha")
            page.click("#kv-remove-btn")
            _wait_list_count(page, 1)
            texts = _list_texts(page)
            assert texts == ["beta=two"], (
                "After removing 'alpha', #kv-list must contain only 'beta=two'; "
                f"got {texts!r}."
            )
            assert _localstorage(page, "alpha") is None, (
                "After Remove, CapacitorStorage.alpha must be removed from localStorage; "
                f"got {_localstorage(page, 'alpha')!r}."
            )

            # Clear all.
            page.click("#kv-clear-btn")
            _wait_list_count(page, 0)
            assert _list_count(page) == 0, (
                "After Clear All, #kv-list must have zero <li> children; "
                f"got {_list_count(page)}."
            )
            assert _localstorage(page, "beta") is None, (
                "After Clear All, CapacitorStorage.beta must be removed from localStorage; "
                f"got {_localstorage(page, 'beta')!r}."
            )

            context.close()
        finally:
            browser.close()
