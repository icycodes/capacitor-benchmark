import json
import os
import re
import socket
import subprocess
import tempfile
import time

import pytest
import requests
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myapp"

PREVIEW_HOST = "127.0.0.1"
PREVIEW_PORT = 4173
PREVIEW_URL = f"http://{PREVIEW_HOST}:{PREVIEW_PORT}/"

API_HOST = "127.0.0.1"
API_PORT = 5174
API_URL = f"http://{API_HOST}:{API_PORT}/data.json"


def _read_capacitor_config():
    """Return (raw_content_or_dict, path, format) for the Capacitor config."""
    ts_path = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    js_path = os.path.join(PROJECT_DIR, "capacitor.config.js")
    json_path = os.path.join(PROJECT_DIR, "capacitor.config.json")

    if os.path.isfile(json_path):
        with open(json_path) as f:
            return json.load(f), json_path, "json"

    for src_path in (ts_path, js_path):
        if os.path.isfile(src_path):
            with open(src_path) as f:
                return f.read(), src_path, "source"

    raise AssertionError(
        "No Capacitor config file (capacitor.config.ts/js/json) found at the project root."
    )


# ---------------------------------------------------------------------------
# Static / config-level verification
# ---------------------------------------------------------------------------


def test_capacitor_http_enabled_in_config():
    """plugins.CapacitorHttp.enabled must be true in the Capacitor config."""
    content, path, fmt = _read_capacitor_config()

    if fmt == "json":
        assert isinstance(content, dict), (
            f"capacitor.config.json at {path} must parse to a JSON object."
        )
        plugins = content.get("plugins")
        assert isinstance(plugins, dict), (
            f"capacitor.config.json at {path} must define a 'plugins' object enabling "
            "CapacitorHttp."
        )
        cap_http = plugins.get("CapacitorHttp")
        assert isinstance(cap_http, dict), (
            f"capacitor.config.json at {path} must define a 'plugins.CapacitorHttp' "
            "object."
        )
        assert cap_http.get("enabled") is True, (
            f"capacitor.config.json at {path} must set plugins.CapacitorHttp.enabled to "
            f"true; got {cap_http.get('enabled')!r}."
        )
    else:
        # Source-level (TS/JS) check: find a CapacitorHttp block with enabled: true.
        pattern = re.compile(
            r"CapacitorHttp\s*:\s*\{[^}]*enabled\s*:\s*true",
            re.DOTALL,
        )
        assert pattern.search(content), (
            f"Capacitor config at {path} must enable CapacitorHttp via a "
            "`plugins: { CapacitorHttp: { enabled: true } }` block."
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
# Long-running fixtures: mock JSON server + Vite preview
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mock_api_server(xprocess):
    """Spin up a deterministic Python http.server that returns {"ok": true} on /data.json."""
    serve_dir = tempfile.mkdtemp(prefix="capacitorhttp_mock_")
    with open(os.path.join(serve_dir, "data.json"), "w") as f:
        json.dump({"ok": True}, f)

    class Starter(ProcessStarter):
        name = "mock_api"
        args = [
            "python3",
            "-m",
            "http.server",
            str(API_PORT),
            "--bind",
            API_HOST,
            "--directory",
            serve_dir,
        ]
        env = os.environ.copy()
        popen_kwargs = {"text": True}
        timeout = 60
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex((API_HOST, API_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)
    # Briefly confirm we can actually serve the file before yielding.
    try:
        response = requests.get(API_URL, timeout=10)
        assert response.status_code == 200, (
            f"Mock API at {API_URL} returned {response.status_code}; expected 200."
        )
    except Exception as exc:  # pragma: no cover - defensive
        info = xprocess.getinfo(Starter.name)
        info.terminate()
        raise AssertionError(f"Mock API failed to come up at {API_URL}: {exc}")

    yield API_URL

    info = xprocess.getinfo(Starter.name)
    info.terminate()


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


# ---------------------------------------------------------------------------
# Markup / HTTP-level verification
# ---------------------------------------------------------------------------


def test_index_served_with_fetch_button_and_status_span(preview_server):
    response = requests.get(preview_server, timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server} returned status {response.status_code}; expected 200."
    )
    body = response.text
    assert re.search(
        r"<button[^>]*\bid\s*=\s*[\"']fetch-btn[\"']", body
    ), (
        "The served index.html must contain a <button> element with id=\"fetch-btn\". "
        f"Got body:\n{body[:1000]}"
    )
    assert re.search(
        r"<span[^>]*\bid\s*=\s*[\"']http-status[\"']", body
    ), (
        "The served index.html must contain a <span> element with id=\"http-status\". "
        f"Got body:\n{body[:1000]}"
    )


# ---------------------------------------------------------------------------
# Browser-driven behavioural verification
# ---------------------------------------------------------------------------


def test_capacitorhttp_get_displays_status_200(preview_server, mock_api_server):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            # Inject the API URL the page must read at click time. The init script
            # runs in every frame before any other script executes.
            context.add_init_script(
                f"window.__API_URL__ = {json.dumps(mock_api_server)};"
            )
            page = context.new_page()
            page.goto(preview_server, wait_until="load")

            page.wait_for_selector("#fetch-btn", state="attached", timeout=10_000)
            page.wait_for_selector("#http-status", state="attached", timeout=10_000)

            # Sanity check: the page sees the injected URL.
            injected_url = page.evaluate("window.__API_URL__")
            assert injected_url == mock_api_server, (
                "Expected window.__API_URL__ to be set by the test fixture; "
                f"got {injected_url!r}."
            )

            page.click("#fetch-btn")

            page.wait_for_function(
                "document.getElementById('http-status') && "
                "document.getElementById('http-status').textContent.trim() === '200'",
                timeout=10_000,
            )

            status_text = page.evaluate(
                "document.getElementById('http-status').textContent.trim()"
            )
            assert status_text == "200", (
                "Expected #http-status text content to become the string '200' after "
                "clicking #fetch-btn (CapacitorHttp.get must resolve with the mock "
                f"server's 200 OK response); got {status_text!r}."
            )

            context.close()
        finally:
            browser.close()
