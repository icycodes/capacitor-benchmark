import json
import os
import re
import socket
import subprocess
import tempfile
import textwrap
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

# Deliberately a *different* origin so that browser-side fetch from the
# Vite preview would be rejected by CORS, demonstrating why CapacitorHttp
# (which bypasses CORS via native HTTP libraries) is the required tool.
MOCK_ALLOW_ORIGIN = "https://example.invalid"

EXPECTED_ITEMS = ["Apple", "Banana", "Cherry"]


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
# Long-running fixtures: mock JSON server (with CORS demo) + Vite preview
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mock_api_server(xprocess):
    """Spin up a deterministic Python http.server serving the items JSON.

    The server intentionally returns ``Access-Control-Allow-Origin`` pointing
    at a different origin than the Vite preview so that a plain browser
    ``fetch`` would be rejected by CORS; the executor must therefore route
    the request through ``CapacitorHttp``.
    """
    serve_dir = tempfile.mkdtemp(prefix="capacitorhttp_items_")
    payload = {"items": [{"name": name} for name in EXPECTED_ITEMS]}
    with open(os.path.join(serve_dir, "data.json"), "w") as f:
        json.dump(payload, f)

    script_path = os.path.join(serve_dir, "_server.py")
    with open(script_path, "w") as f:
        f.write(textwrap.dedent(
            f"""
            import http.server
            import os

            SERVE_DIR = {serve_dir!r}
            HOST = {API_HOST!r}
            PORT = {API_PORT}
            ALLOW_ORIGIN = {MOCK_ALLOW_ORIGIN!r}


            class Handler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=SERVE_DIR, **kwargs)

                def end_headers(self):
                    # Intentionally restrict CORS to a non-matching origin so
                    # that browser-side fetch from the Vite preview is denied.
                    self.send_header("Access-Control-Allow-Origin", ALLOW_ORIGIN)
                    self.send_header("Vary", "Origin")
                    super().end_headers()

                def guess_type(self, path):
                    if path.endswith(".json"):
                        return "application/json"
                    return super().guess_type(path)


            if __name__ == "__main__":
                with http.server.ThreadingHTTPServer((HOST, PORT), Handler) as httpd:
                    httpd.serve_forever()
            """
        ).strip() + "\n")

    class Starter(ProcessStarter):
        name = "mock_api"
        args = ["python3", script_path]
        env = os.environ.copy()
        popen_kwargs = {"text": True}
        timeout = 60
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex((API_HOST, API_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)

    # Sanity-check that the mock endpoint serves the expected payload and
    # exposes the (intentionally non-matching) CORS header.
    try:
        response = requests.get(API_URL, timeout=10)
        assert response.status_code == 200, (
            f"Mock API at {API_URL} returned {response.status_code}; expected 200."
        )
        assert response.json() == payload, (
            f"Mock API payload mismatch. Got: {response.text!r}"
        )
        allow_origin = response.headers.get("Access-Control-Allow-Origin")
        assert allow_origin == MOCK_ALLOW_ORIGIN, (
            "Mock API should advertise a CORS allow-origin distinct from the Vite "
            f"preview origin; got {allow_origin!r}."
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


def test_index_served_with_fetch_button_and_items_list(preview_server):
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
        r"<ul[^>]*\bid\s*=\s*[\"']items[\"']", body
    ), (
        "The served index.html must contain a <ul> element with id=\"items\". "
        f"Got body:\n{body[:1000]}"
    )


# ---------------------------------------------------------------------------
# Browser-driven behavioural verification
# ---------------------------------------------------------------------------


def test_capacitorhttp_get_renders_items_list(preview_server, mock_api_server):
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
            page.wait_for_selector("#items", state="attached", timeout=10_000)

            # Sanity check: the page sees the injected URL.
            injected_url = page.evaluate("window.__API_URL__")
            assert injected_url == mock_api_server, (
                "Expected window.__API_URL__ to be set by the test fixture; "
                f"got {injected_url!r}."
            )

            page.click("#fetch-btn")

            # Wait until exactly three <li> children are rendered with the
            # expected text content in order.
            page.wait_for_function(
                """
                (expected) => {
                    const list = document.getElementById('items');
                    if (!list) return false;
                    const items = list.querySelectorAll('li');
                    if (items.length !== expected.length) return false;
                    for (let i = 0; i < expected.length; i++) {
                        if ((items[i].textContent || '').trim() !== expected[i]) {
                            return false;
                        }
                    }
                    return true;
                }
                """,
                arg=EXPECTED_ITEMS,
                timeout=10_000,
            )

            rendered = page.evaluate(
                "Array.from(document.getElementById('items').querySelectorAll('li'))"
                ".map(el => (el.textContent || '').trim())"
            )
            assert rendered == EXPECTED_ITEMS, (
                "Expected #items to contain exactly the three <li> children "
                f"{EXPECTED_ITEMS!r} (in order) after clicking #fetch-btn; "
                f"got {rendered!r}."
            )

            context.close()
        finally:
            browser.close()
