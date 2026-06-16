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
EXPECTED_TEXT = "benchmark text"


# ---------------------------------------------------------------------------
# Static / config-level verification
# ---------------------------------------------------------------------------


def test_package_json_declares_clipboard_plugin():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), f"package.json not found at {pkg_path}."
    with open(pkg_path) as f:
        pkg = json.load(f)
    deps = {}
    deps.update(pkg.get("dependencies", {}) or {})
    deps.update(pkg.get("devDependencies", {}) or {})
    assert "@capacitor/clipboard" in deps, (
        "Expected '@capacitor/clipboard' to be declared in dependencies or "
        f"devDependencies of {pkg_path}. Found keys: {sorted(deps)}"
    )


def test_clipboard_plugin_installed_at_major_8():
    installed_pkg = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "clipboard", "package.json"
    )
    assert os.path.isfile(installed_pkg), (
        f"Expected @capacitor/clipboard to be installed at {installed_pkg}. "
        "Did `npm install` run after adding the dependency?"
    )
    with open(installed_pkg) as f:
        data = json.load(f)
    version = str(data.get("version", ""))
    assert version, (
        f"Installed @capacitor/clipboard package.json has no version field: {data!r}"
    )
    major = version.split(".")[0]
    assert major == "8", (
        f"Expected installed @capacitor/clipboard to be version 8.x; found {version!r}. "
        "Capacitor v8 requires plugins at major version 8."
    )


def test_clipboard_plugin_declared_version_major_8_in_package_json():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg_path) as f:
        pkg = json.load(f)
    deps = {}
    deps.update(pkg.get("dependencies", {}) or {})
    deps.update(pkg.get("devDependencies", {}) or {})
    declared = deps.get("@capacitor/clipboard", "")
    # Strip common range prefixes/leading whitespace so we can inspect the major.
    cleaned = declared.strip().lstrip("^~>=< ").strip()
    leading_major = cleaned.split(".")[0] if cleaned else ""
    assert leading_major == "8", (
        "Expected the declared @capacitor/clipboard version in package.json to "
        f"target major version 8; got {declared!r}."
    )


def test_npm_build_succeeds_and_produces_index_html():
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
        f"Expected production build output at {dist_index}."
    )


def test_capacitor_sync_succeeds():
    result = subprocess.run(
        ["npx", "--no-install", "cap", "sync"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Expected `npx cap sync` to exit 0 after the production build.\n"
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


def test_index_served_with_required_elements(preview_server):
    response = requests.get(preview_server, timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server} returned status {response.status_code}; expected 200."
    )
    body = response.text
    assert re.search(
        r"<input\b[^>]*\bid\s*=\s*[\"']clip-input[\"']", body
    ), (
        "The served index.html must contain an <input> element with "
        f'id="clip-input". First 1000 chars of body:\n{body[:1000]}'
    )
    assert re.search(
        r"<button\b[^>]*\bid\s*=\s*[\"']clip-write-btn[\"']", body
    ), (
        "The served index.html must contain a <button> element with "
        f'id="clip-write-btn". First 1000 chars of body:\n{body[:1000]}'
    )
    assert re.search(
        r"<button\b[^>]*\bid\s*=\s*[\"']clip-read-btn[\"']", body
    ), (
        "The served index.html must contain a <button> element with "
        f'id="clip-read-btn". First 1000 chars of body:\n{body[:1000]}'
    )
    assert re.search(
        r"<span\b[^>]*\bid\s*=\s*[\"']clip-output[\"']", body
    ), (
        "The served index.html must contain a <span> element with "
        f'id="clip-output". First 1000 chars of body:\n{body[:1000]}'
    )


# ---------------------------------------------------------------------------
# Browser-driven behavioural verification
# ---------------------------------------------------------------------------


def _text(page, selector: str) -> str:
    return page.evaluate(
        "(sel) => (document.querySelector(sel)?.textContent ?? '')",
        selector,
    )


def test_clipboard_write_then_read_round_trip(preview_server):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                permissions=["clipboard-read", "clipboard-write"],
            )
            page = context.new_page()
            page.goto(preview_server, wait_until="load")
            page.wait_for_selector("#clip-input", state="visible", timeout=10_000)
            page.wait_for_selector("#clip-write-btn", state="visible", timeout=10_000)
            page.wait_for_selector("#clip-read-btn", state="visible", timeout=10_000)
            page.wait_for_selector("#clip-output", state="attached", timeout=10_000)

            # Fill the input, click write, wait 300 ms.
            page.fill("#clip-input", EXPECTED_TEXT)
            page.click("#clip-write-btn")
            page.wait_for_timeout(300)

            # Click read and wait for the output span to reflect the value.
            page.click("#clip-read-btn")
            page.wait_for_function(
                "(want) => document.querySelector('#clip-output')?.textContent === want",
                arg=EXPECTED_TEXT,
                timeout=10_000,
            )
            actual_span = _text(page, "#clip-output")
            assert actual_span == EXPECTED_TEXT, (
                "After filling #clip-input with the expected text, clicking "
                "#clip-write-btn, then clicking #clip-read-btn, "
                f"#clip-output must equal {EXPECTED_TEXT!r}; got {actual_span!r}."
            )

            # Confirm the value really landed on the system clipboard.
            clipboard_contents = page.evaluate(
                "() => navigator.clipboard.readText()"
            )
            assert clipboard_contents == EXPECTED_TEXT, (
                "After clicking #clip-write-btn, navigator.clipboard.readText() "
                f"must return {EXPECTED_TEXT!r}; got {clipboard_contents!r}. "
                "This proves the Capacitor Clipboard plugin actually wrote to the "
                "system clipboard."
            )

            context.close()
        finally:
            browser.close()
