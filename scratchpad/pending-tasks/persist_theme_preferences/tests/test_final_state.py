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
        # Tolerant regex extraction of the three required fields.
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
    assert cfg.get("appName") == "Theme Demo", (
        f"capacitor config at {path} must set appName to 'Theme Demo'; got {cfg.get('appName')!r}."
    )
    assert cfg.get("appId") == "com.example.themedemo", (
        f"capacitor config at {path} must set appId to 'com.example.themedemo'; "
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


def test_dist_index_html_exists():
    dist_index = os.path.join(PROJECT_DIR, "dist", "index.html")
    assert os.path.isfile(dist_index), (
        f"Expected production build output at {dist_index}. "
        "Make sure `npm run build` succeeded."
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
    # Give Vite a brief moment to fully bind even after the port is open.
    time.sleep(1.0)
    yield PREVIEW_URL
    info = xprocess.getinfo(Starter.name)
    info.terminate()


def test_index_served_with_toggle_button(preview_server):
    response = requests.get(preview_server, timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server} returned status {response.status_code}; expected 200."
    )
    body = response.text
    assert re.search(r"id\s*=\s*[\"']theme-toggle[\"']", body), (
        "The served index.html must contain an element with id=\"theme-toggle\". "
        f"Got body:\n{body[:1000]}"
    )


# ---------------------------------------------------------------------------
# Browser-driven behavioural verification
# ---------------------------------------------------------------------------


def _check_dark_class(page) -> bool:
    return page.evaluate("document.body.classList.contains('dark')")


def _read_preferences_value(page) -> str | None:
    # The Capacitor Preferences plugin uses the `CapacitorStorage.` prefix in its
    # localStorage fallback (the default storage group is `CapacitorStorage`).
    return page.evaluate(
        "window.localStorage.getItem('CapacitorStorage.user_theme')"
    )


def test_theme_toggle_flow(preview_server):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            # Fresh context => empty localStorage by default.
            context = browser.new_context()
            page = context.new_page()
            page.goto(preview_server, wait_until="load")
            page.wait_for_selector("#theme-toggle", state="visible", timeout=10_000)
            # Allow the load handler to run.
            page.wait_for_timeout(300)

            assert _check_dark_class(page) is False, (
                "On first load with no stored preference, the <body> element must NOT have "
                "the 'dark' class (default theme is light)."
            )

            # Toggle to dark.
            page.click("#theme-toggle")
            page.wait_for_function(
                "document.body.classList.contains('dark') === true",
                timeout=5_000,
            )
            assert _check_dark_class(page) is True, (
                "After clicking #theme-toggle once, the <body> element must have the 'dark' class."
            )

            stored = _read_preferences_value(page)
            assert stored == "dark", (
                "After toggling to dark, the Capacitor Preferences fallback key "
                "'CapacitorStorage.user_theme' must equal 'dark'; "
                f"got {stored!r}."
            )

            # Reload — persistence check.
            page.reload(wait_until="load")
            page.wait_for_selector("#theme-toggle", state="visible", timeout=10_000)
            page.wait_for_timeout(300)
            assert _check_dark_class(page) is True, (
                "After reloading the page, the persisted 'dark' theme must still be "
                "applied (the <body> element should keep the 'dark' class)."
            )

            # Toggle back to light.
            page.click("#theme-toggle")
            page.wait_for_function(
                "document.body.classList.contains('dark') === false",
                timeout=5_000,
            )
            assert _check_dark_class(page) is False, (
                "After clicking #theme-toggle again, the <body> element must no longer "
                "have the 'dark' class."
            )

            stored = _read_preferences_value(page)
            assert stored == "light", (
                "After toggling back to light, the Capacitor Preferences fallback key "
                "'CapacitorStorage.user_theme' must equal 'light'; "
                f"got {stored!r}."
            )

            # Reload — persistence check for the light state.
            page.reload(wait_until="load")
            page.wait_for_selector("#theme-toggle", state="visible", timeout=10_000)
            page.wait_for_timeout(300)
            assert _check_dark_class(page) is False, (
                "After reloading the page following a switch back to light, the <body> "
                "element must NOT have the 'dark' class."
            )

            context.close()
        finally:
            browser.close()
