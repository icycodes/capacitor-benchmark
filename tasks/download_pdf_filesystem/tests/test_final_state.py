import hashlib
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
FIXTURE_PDF = os.path.join(PROJECT_DIR, "public", "sample.pdf")


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

        def find(field: str):
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


def _expected_pdf_metadata():
    assert os.path.isfile(FIXTURE_PDF), (
        f"Fixture PDF not found at {FIXTURE_PDF}; the bootstrap environment is broken."
    )
    with open(FIXTURE_PDF, "rb") as f:
        data = f.read()
    return len(data), hashlib.sha256(data).hexdigest(), data


# ---------------------------------------------------------------------------
# Static / config-level verification
# ---------------------------------------------------------------------------


def test_capacitor_config_values():
    cfg, path = _read_capacitor_config()
    assert cfg.get("appName") == "Filesystem Demo", (
        f"capacitor config at {path} must set appName to 'Filesystem Demo'; "
        f"got {cfg.get('appName')!r}."
    )
    assert cfg.get("appId") == "com.example.fsdemo", (
        f"capacitor config at {path} must set appId to 'com.example.fsdemo'; "
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
    deps = {}
    deps.update(pkg.get("dependencies", {}) or {})
    deps.update(pkg.get("devDependencies", {}) or {})
    for required in ("@capacitor/core", "@capacitor/cli", "@capacitor/filesystem"):
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


def test_dist_sample_pdf_exists():
    dist_pdf = os.path.join(PROJECT_DIR, "dist", "sample.pdf")
    assert os.path.isfile(dist_pdf), (
        f"Expected the fixture PDF to be copied to {dist_pdf} during the build. "
        "Files inside Vite's `public/` directory are copied verbatim to the build output."
    )


def test_dist_sample_pdf_bytes_match_fixture():
    expected_size, expected_sha, _ = _expected_pdf_metadata()
    dist_pdf = os.path.join(PROJECT_DIR, "dist", "sample.pdf")
    with open(dist_pdf, "rb") as f:
        data = f.read()
    assert len(data) == expected_size, (
        f"{dist_pdf} length {len(data)} does not match fixture length {expected_size}."
    )
    assert hashlib.sha256(data).hexdigest() == expected_sha, (
        f"{dist_pdf} SHA-256 does not match the public/sample.pdf fixture."
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


def test_index_served_with_required_elements(preview_server):
    response = requests.get(preview_server, timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server} returned status {response.status_code}; expected 200."
    )
    body = response.text
    for required_id in ("download-pdf", "download-status", "file-size", "file-sha256"):
        assert re.search(rf"id\s*=\s*[\"']{re.escape(required_id)}[\"']", body), (
            f"The served index.html must contain an element with id=\"{required_id}\". "
            f"Got body (first 1000 chars):\n{body[:1000]}"
        )


def test_preview_serves_sample_pdf(preview_server):
    expected_size, expected_sha, _ = _expected_pdf_metadata()
    response = requests.get(preview_server + "sample.pdf", timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server}sample.pdf returned status {response.status_code}; expected 200."
    )
    body = response.content
    assert len(body) == expected_size, (
        f"Served sample.pdf has {len(body)} bytes; expected {expected_size}."
    )
    assert hashlib.sha256(body).hexdigest() == expected_sha, (
        "Served sample.pdf SHA-256 does not match the fixture."
    )


# ---------------------------------------------------------------------------
# Browser-driven behavioural verification
# ---------------------------------------------------------------------------


def _wait_for_status(page, expected: str, timeout_ms: int = 20_000):
    page.wait_for_function(
        "(want) => document.querySelector('#download-status')?.textContent?.trim() === want",
        arg=expected,
        timeout=timeout_ms,
    )


def _text(page, selector: str) -> str:
    return page.evaluate(
        "(sel) => (document.querySelector(sel)?.textContent ?? '').trim()",
        selector,
    )


def test_download_pdf_filesystem_flow(preview_server):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    expected_size, expected_sha, _ = _expected_pdf_metadata()
    expected_size_str = str(expected_size)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            # Fresh context => empty IndexedDB by default.
            context = browser.new_context()
            page = context.new_page()
            page.goto(preview_server, wait_until="load")
            page.wait_for_selector("#download-pdf", state="visible", timeout=10_000)
            page.wait_for_selector("#download-status", state="attached", timeout=10_000)
            page.wait_for_selector("#file-size", state="attached", timeout=10_000)
            page.wait_for_selector("#file-sha256", state="attached", timeout=10_000)
            # Give the load handler a brief moment to populate the initial state.
            page.wait_for_timeout(300)

            assert _text(page, "#download-status") == "idle", (
                "On first load, #download-status must contain the text 'idle'; "
                f"got {_text(page, '#download-status')!r}."
            )
            assert _text(page, "#file-size") == "", (
                "On first load, #file-size must be empty; "
                f"got {_text(page, '#file-size')!r}."
            )
            assert _text(page, "#file-sha256") == "", (
                "On first load, #file-sha256 must be empty; "
                f"got {_text(page, '#file-sha256')!r}."
            )

            # First download cycle.
            page.click("#download-pdf")
            _wait_for_status(page, "saved")
            assert _text(page, "#download-status") == "saved", (
                "After clicking #download-pdf, #download-status must transition to 'saved'; "
                f"got {_text(page, '#download-status')!r}."
            )
            assert _text(page, "#file-size") == expected_size_str, (
                "After a successful download, #file-size must show the byte length of the "
                f"persisted PDF ({expected_size_str}); got {_text(page, '#file-size')!r}."
            )
            sha_text = _text(page, "#file-sha256").lower()
            assert sha_text == expected_sha, (
                "After a successful download, #file-sha256 must show the lowercase hex "
                f"SHA-256 of the persisted PDF ({expected_sha}); got {sha_text!r}."
            )

            # Reload — UI should reset, but the file must remain persisted.
            page.reload(wait_until="load")
            page.wait_for_selector("#download-pdf", state="visible", timeout=10_000)
            page.wait_for_timeout(300)
            assert _text(page, "#download-status") == "idle", (
                "After a reload, #download-status must reset to 'idle'; "
                f"got {_text(page, '#download-status')!r}."
            )
            assert _text(page, "#file-size") == "", (
                "After a reload, #file-size must be empty until the next download; "
                f"got {_text(page, '#file-size')!r}."
            )
            assert _text(page, "#file-sha256") == "", (
                "After a reload, #file-sha256 must be empty until the next download; "
                f"got {_text(page, '#file-sha256')!r}."
            )

            # Second download cycle — same outputs.
            page.click("#download-pdf")
            _wait_for_status(page, "saved")
            assert _text(page, "#download-status") == "saved", (
                "On the second download click, #download-status must reach 'saved' again; "
                f"got {_text(page, '#download-status')!r}."
            )
            assert _text(page, "#file-size") == expected_size_str, (
                "On the second download, #file-size must again equal the persisted PDF size "
                f"({expected_size_str}); got {_text(page, '#file-size')!r}."
            )
            sha_text = _text(page, "#file-sha256").lower()
            assert sha_text == expected_sha, (
                "On the second download, #file-sha256 must again equal the persisted PDF "
                f"SHA-256 ({expected_sha}); got {sha_text!r}."
            )

            context.close()
        finally:
            browser.close()
