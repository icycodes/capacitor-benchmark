import json
import os
import re
import shutil
import socket
import subprocess

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


def _semver_major(version_str):
    """Return the integer semver major component for an arbitrary spec."""
    if not isinstance(version_str, str):
        return None
    cleaned = version_str.strip().lstrip("^~=>< vV")
    match = re.match(r"(\d+)", cleaned)
    return int(match.group(1)) if match else None


# ---------------------------------------------------------------------------
# Truth Step 1: package.json declares @capacitor/share at major 8
# ---------------------------------------------------------------------------


def test_share_dependency_at_major_8():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), (
        f"Expected package.json at {pkg_path} after the task completes."
    )
    with open(pkg_path) as f:
        data = json.load(f)
    deps = data.get("dependencies") or {}
    assert isinstance(deps, dict), "package.json 'dependencies' must be an object."
    assert "@capacitor/share" in deps, (
        "Expected '@capacitor/share' to be declared in package.json "
        "'dependencies' after the task completes; got dependencies="
        f"{sorted(deps.keys())}."
    )

    installed_pkg_path = os.path.join(
        PROJECT_DIR,
        "node_modules",
        "@capacitor",
        "share",
        "package.json",
    )
    if os.path.isfile(installed_pkg_path):
        with open(installed_pkg_path) as f:
            installed = json.load(f)
        installed_version = installed.get("version")
        resolved_major = _semver_major(installed_version)
        assert resolved_major == 8, (
            "Expected the installed '@capacitor/share' to be at major version 8, "
            f"but {installed_pkg_path} reports version={installed_version!r}."
        )
    else:
        spec_major = _semver_major(deps["@capacitor/share"])
        assert spec_major == 8, (
            "Expected package.json to pin '@capacitor/share' to a v8 specifier; "
            f"got {deps['@capacitor/share']!r}."
        )


# ---------------------------------------------------------------------------
# Truth Steps 2 & 3: production build + cap sync
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
# Truth Steps 4 & 5: served HTML + Playwright click & payload check
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def preview_server(xprocess):
    class Starter(ProcessStarter):
        name = "vite_preview_share"
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


def test_share_button_visible_in_dom(preview_server):
    """The served page (after JS executes) must render <button id="share-btn">."""
    response = requests.get(preview_server, timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server} returned status {response.status_code}; expected 200."
    )

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            page = context.new_page()
            page.goto(preview_server, wait_until="load", timeout=30000)
            # Wait for the button to be attached to the DOM (regardless of whether
            # it is part of the static HTML or injected by src/main.ts).
            page.wait_for_selector("#share-btn", state="attached", timeout=15000)
            tag_name = page.eval_on_selector(
                "#share-btn", "el => el.tagName.toLowerCase()"
            )
            assert tag_name == "button", (
                "Expected the #share-btn element to be a <button>; "
                f"found <{tag_name}>."
            )
        finally:
            browser.close()


def test_click_share_button_invokes_navigator_share_with_expected_payload(preview_server):
    """Clicking #share-btn must call navigator.share exactly once with title/text."""
    from playwright.sync_api import sync_playwright

    init_script = """
        window.__shareCalls = [];
        Object.defineProperty(navigator, 'share', {
            configurable: true,
            writable: true,
            value: async (data) => { window.__shareCalls.push(data); }
        });
        Object.defineProperty(navigator, 'canShare', {
            configurable: true,
            writable: true,
            value: (data) => true
        });
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            context.add_init_script(init_script)
            page = context.new_page()
            page.goto(preview_server, wait_until="load", timeout=30000)
            page.wait_for_selector("#share-btn", state="visible", timeout=15000)
            page.click("#share-btn")
            page.wait_for_timeout(500)

            share_calls = page.evaluate("window.__shareCalls")

            assert isinstance(share_calls, list), (
                "Expected window.__shareCalls to be an array after clicking "
                f"#share-btn; got: {share_calls!r}"
            )
            assert len(share_calls) == 1, (
                "Expected exactly one Share.share invocation after a single click "
                f"on #share-btn; got {len(share_calls)} calls: {share_calls!r}"
            )

            payload = share_calls[0]
            assert isinstance(payload, dict), (
                "Expected the captured Share payload to be an object; "
                f"got: {payload!r}"
            )
            assert payload.get("title") == "Demo", (
                "Expected captured Share payload.title === 'Demo'; "
                f"got payload={payload!r}"
            )
            assert payload.get("text") == "Hello from Capacitor", (
                "Expected captured Share payload.text === 'Hello from Capacitor'; "
                f"got payload={payload!r}"
            )
        finally:
            browser.close()
