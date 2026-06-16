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
EXPECTED_TEXT = "Hello Capacitor"


# ---------------------------------------------------------------------------
# Static / config-level verification
# ---------------------------------------------------------------------------


def test_package_json_declares_filesystem_plugin():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), f"package.json not found at {pkg_path}."
    with open(pkg_path) as f:
        pkg = json.load(f)
    deps = {}
    deps.update(pkg.get("dependencies", {}) or {})
    deps.update(pkg.get("devDependencies", {}) or {})
    assert "@capacitor/filesystem" in deps, (
        "Expected '@capacitor/filesystem' to be declared in dependencies or "
        f"devDependencies of {pkg_path}. Found keys: {sorted(deps)}"
    )


def test_filesystem_plugin_installed_at_major_8():
    installed_pkg = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "filesystem", "package.json"
    )
    assert os.path.isfile(installed_pkg), (
        f"Expected @capacitor/filesystem to be installed at {installed_pkg}. "
        "Did `npm install` run after adding the dependency?"
    )
    with open(installed_pkg) as f:
        data = json.load(f)
    version = str(data.get("version", ""))
    assert version, f"Installed @capacitor/filesystem package.json has no version field: {data!r}"
    major = version.split(".")[0]
    assert major == "8", (
        f"Expected installed @capacitor/filesystem to be version 8.x; found {version!r}. "
        "Capacitor v8 requires plugins at major version 8."
    )


def test_npm_build_succeeds_and_produces_index_html():
    # `npm run build` must be idempotent; running it as part of the verifier
    # ensures the produced bundle reflects the executor's final source state.
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
    # The button and span tags must specifically be present (not arbitrary divs).
    assert re.search(
        r"<button\b[^>]*\bid\s*=\s*[\"']write-btn[\"']", body
    ), (
        "The served index.html must contain a <button> element with "
        f'id="write-btn". First 1000 chars of body:\n{body[:1000]}'
    )
    assert re.search(
        r"<button\b[^>]*\bid\s*=\s*[\"']read-btn[\"']", body
    ), (
        "The served index.html must contain a <button> element with "
        f'id="read-btn". First 1000 chars of body:\n{body[:1000]}'
    )
    assert re.search(
        r"<span\b[^>]*\bid\s*=\s*[\"']file-content[\"']", body
    ), (
        "The served index.html must contain a <span> element with "
        f'id="file-content". First 1000 chars of body:\n{body[:1000]}'
    )


# ---------------------------------------------------------------------------
# Browser-driven behavioural verification
# ---------------------------------------------------------------------------


def _text(page, selector: str) -> str:
    return page.evaluate(
        "(sel) => (document.querySelector(sel)?.textContent ?? '')",
        selector,
    )


def test_filesystem_write_then_read_populates_file_content(preview_server):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            page = context.new_page()
            page.goto(preview_server, wait_until="load")
            page.wait_for_selector("#write-btn", state="visible", timeout=10_000)
            page.wait_for_selector("#read-btn", state="visible", timeout=10_000)
            page.wait_for_selector("#file-content", state="attached", timeout=10_000)

            # Click write -> wait 300 ms -> click read.
            page.click("#write-btn")
            page.wait_for_timeout(300)
            page.click("#read-btn")

            # Wait for #file-content to strictly equal the expected text.
            page.wait_for_function(
                "(want) => document.querySelector('#file-content')?.textContent === want",
                arg=EXPECTED_TEXT,
                timeout=10_000,
            )
            actual = _text(page, "#file-content")
            assert actual == EXPECTED_TEXT, (
                "After clicking #write-btn then #read-btn, "
                f"#file-content must equal {EXPECTED_TEXT!r}; got {actual!r}."
            )

            # Reload the page (same context => IndexedDB preserved).
            page.reload(wait_until="load")
            page.wait_for_selector("#read-btn", state="visible", timeout=10_000)
            page.wait_for_selector("#file-content", state="attached", timeout=10_000)

            # The span should be reset on reload; if not, we still proceed
            # because the only contractual requirement is that clicking
            # #read-btn alone yields the persisted text.
            page.click("#read-btn")
            page.wait_for_function(
                "(want) => document.querySelector('#file-content')?.textContent === want",
                arg=EXPECTED_TEXT,
                timeout=10_000,
            )
            actual_after_reload = _text(page, "#file-content")
            assert actual_after_reload == EXPECTED_TEXT, (
                "After a page reload (without clicking #write-btn again), "
                f"clicking #read-btn must populate #file-content with {EXPECTED_TEXT!r}; "
                f"got {actual_after_reload!r}. This proves the file was persisted "
                "by Capacitor's Filesystem plugin across reloads."
            )

            context.close()
        finally:
            browser.close()
