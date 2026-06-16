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


# ---------------------------------------------------------------------------
# Static / config-level verification
# ---------------------------------------------------------------------------


def test_package_json_lists_capacitor_network():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), f"package.json not found at {pkg_path}."
    with open(pkg_path) as f:
        pkg = json.load(f)
    deps: dict[str, str] = {}
    deps.update(pkg.get("dependencies", {}) or {})
    deps.update(pkg.get("devDependencies", {}) or {})
    assert "@capacitor/network" in deps, (
        "Expected '@capacitor/network' to be declared in dependencies or "
        f"devDependencies of {pkg_path}. Found keys: {sorted(deps)}"
    )


def test_installed_capacitor_network_major_version_is_8():
    installed_pkg = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "network", "package.json"
    )
    assert os.path.isfile(installed_pkg), (
        f"@capacitor/network is not installed under node_modules at {installed_pkg}. "
        "Make sure `npm install @capacitor/network` succeeded."
    )
    with open(installed_pkg) as f:
        data = json.load(f)
    version = str(data.get("version", "")).strip()
    assert version, (
        f"Could not read version from {installed_pkg}; got {data!r}."
    )
    major_str = version.split(".")[0].lstrip("v")
    assert major_str.isdigit() and int(major_str) == 8, (
        f"Expected installed @capacitor/network major version to be 8, "
        f"got version {version!r}."
    )


def test_npm_run_build_succeeds_and_produces_dist_index():
    # Always rebuild to guarantee dist/index.html reflects the executor's source.
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Expected `npm run build` to exit with code 0.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    dist_index = os.path.join(PROJECT_DIR, "dist", "index.html")
    assert os.path.isfile(dist_index), (
        f"Expected production build output at {dist_index} after `npm run build`."
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
        "Expected `npx cap sync` to exit with code 0 after the production build.\n"
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


def test_preview_server_responds_with_200(preview_server):
    response = requests.get(preview_server, timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server} returned status {response.status_code}; expected 200."
    )


# ---------------------------------------------------------------------------
# Browser-driven behavioural verification
# ---------------------------------------------------------------------------


def _wait_for_net_status_text(page, expected: str, timeout_ms: int = 5000) -> None:
    """Wait until #net-status.textContent equals `expected`, or fail."""
    js_expected = json.dumps(expected)
    page.wait_for_function(
        f"document.querySelector('#net-status') && "
        f"document.querySelector('#net-status').textContent.trim() === {js_expected}",
        timeout=timeout_ms,
    )


def test_network_status_indicator_flow(preview_server):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            # Default context is online.
            context = browser.new_context()
            page = context.new_page()
            page.goto(preview_server, wait_until="load")

            # There must be exactly one #net-status element on the page.
            page.wait_for_selector("#net-status", state="attached", timeout=10_000)
            count = page.locator("#net-status").count()
            assert count == 1, (
                "Expected exactly one element matching '#net-status' on the page, "
                f"found {count}."
            )

            # Initial state: online.
            _wait_for_net_status_text(page, "online", timeout_ms=5000)
            current = page.evaluate(
                "document.querySelector('#net-status').textContent"
            )
            assert current.strip() == "online", (
                "On initial load with an online browser context, "
                "#net-status.textContent must equal 'online'; "
                f"got {current!r}."
            )

            # Flip context offline, expect the indicator to follow within 5s.
            context.set_offline(True)
            _wait_for_net_status_text(page, "offline", timeout_ms=5000)
            current = page.evaluate(
                "document.querySelector('#net-status').textContent"
            )
            assert current.strip() == "offline", (
                "After context.set_offline(True), #net-status.textContent must "
                f"transition to 'offline' within 5 seconds; got {current!r}."
            )

            # Flip back online, expect the indicator to follow within 5s.
            context.set_offline(False)
            _wait_for_net_status_text(page, "online", timeout_ms=5000)
            current = page.evaluate(
                "document.querySelector('#net-status').textContent"
            )
            assert current.strip() == "online", (
                "After context.set_offline(False), #net-status.textContent must "
                f"transition back to 'online' within 5 seconds; got {current!r}."
            )

            context.close()
        finally:
            browser.close()
