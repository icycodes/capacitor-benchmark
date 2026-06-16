import json
import os
import re
import shutil
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _semver_major(version_str):
    """Return the integer semver major component for an arbitrary spec."""
    if not isinstance(version_str, str):
        return None
    cleaned = version_str.strip().lstrip("^~=>< vV")
    match = re.match(r"(\d+)", cleaned)
    return int(match.group(1)) if match else None


# ---------------------------------------------------------------------------
# Truth Step 1: package.json declares @capacitor/app at major 8
# ---------------------------------------------------------------------------


def test_app_dependency_at_major_8():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), (
        f"Expected package.json at {pkg_path} after the task completes."
    )
    with open(pkg_path) as f:
        data = json.load(f)
    deps = data.get("dependencies") or {}
    assert isinstance(deps, dict), "package.json 'dependencies' must be an object."
    assert "@capacitor/app" in deps, (
        "Expected '@capacitor/app' to be declared in package.json "
        "'dependencies' after the task completes; got dependencies="
        f"{sorted(deps.keys())}."
    )

    # Prefer the installed version from node_modules when available, otherwise
    # fall back to the specifier string in package.json itself.
    installed_pkg_path = os.path.join(
        PROJECT_DIR,
        "node_modules",
        "@capacitor",
        "app",
        "package.json",
    )
    if os.path.isfile(installed_pkg_path):
        with open(installed_pkg_path) as f:
            installed = json.load(f)
        installed_version = installed.get("version")
        resolved_major = _semver_major(installed_version)
        assert resolved_major == 8, (
            "Expected the installed '@capacitor/app' to be at major version 8, "
            f"but {installed_pkg_path} reports version={installed_version!r}."
        )
    else:
        spec_major = _semver_major(deps["@capacitor/app"])
        assert spec_major == 8, (
            "Expected package.json to pin '@capacitor/app' to a v8 specifier; "
            f"got {deps['@capacitor/app']!r}."
        )


# ---------------------------------------------------------------------------
# Truth Step 2 & 3: production build + cap sync
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
# Truth Steps 4 & 5: preview HTTP 200 + headless browser behaviour
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


def test_preview_serves_html(preview_server):
    response = requests.get(preview_server, timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server} returned status {response.status_code}; expected 200."
    )


def _wait_for_text(page, selector, expected, timeout_ms=5000):
    """Poll page.locator(selector).text_content() until it equals expected.

    Returns the (last_observed, succeeded) tuple. We avoid playwright's
    `expect()` helper to keep dependencies minimal and to surface the actual
    value we saw at timeout.
    """
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    last_observed = None
    while time.monotonic() < deadline:
        try:
            last_observed = page.locator(selector).text_content()
        except Exception:
            last_observed = None
        if last_observed == expected:
            return last_observed, True
        time.sleep(0.05)
    return last_observed, False


def test_app_state_listener_drives_text_content(preview_server):
    from playwright.sync_api import sync_playwright

    toggle_hidden_true = (
        "Object.defineProperty(document, 'hidden', "
        "{ value: true, configurable: true }); "
        "document.dispatchEvent(new Event('visibilitychange'))"
    )
    toggle_hidden_false = (
        "Object.defineProperty(document, 'hidden', "
        "{ value: false, configurable: true }); "
        "document.dispatchEvent(new Event('visibilitychange'))"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        try:
            context = browser.new_context()
            page = context.new_page()
            page.goto(preview_server, wait_until="load", timeout=30000)

            # Subcheck (a): #app-state must exist and be "active" on load.
            page.wait_for_selector("#app-state", state="attached", timeout=5000)
            initial = page.locator("#app-state").text_content()
            assert initial == "active", (
                "Expected #app-state.textContent to equal 'active' on initial load, "
                f"got {initial!r}."
            )

            # Subcheck (b): dispatching visibilitychange with hidden=true must
            # cause #app-state.textContent to become 'inactive' within 5s.
            page.evaluate(toggle_hidden_true)
            observed, ok = _wait_for_text(
                page, "#app-state", "inactive", timeout_ms=5000
            )
            assert ok, (
                "Expected #app-state.textContent to become 'inactive' within 5s after "
                "dispatching a visibilitychange with document.hidden=true; "
                f"last observed value: {observed!r}."
            )

            # Subcheck (c): dispatching visibilitychange with hidden=false must
            # restore #app-state.textContent to 'active' within 5s.
            page.evaluate(toggle_hidden_false)
            observed, ok = _wait_for_text(
                page, "#app-state", "active", timeout_ms=5000
            )
            assert ok, (
                "Expected #app-state.textContent to return to 'active' within 5s "
                "after dispatching a visibilitychange with document.hidden=false; "
                f"last observed value: {observed!r}."
            )
        finally:
            browser.close()
