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

        def find(field: str):
            m = re.search(rf"{field}\s*:\s*['\"]([^'\"]+)['\"]", content)
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
    assert cfg.get("appName") == "Device Info Dual", (
        f"capacitor config at {path} must set appName to 'Device Info Dual'; "
        f"got {cfg.get('appName')!r}."
    )
    assert cfg.get("appId") == "com.example.deviceinfodual", (
        f"capacitor config at {path} must set appId to 'com.example.deviceinfodual'; "
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
    deps: dict = {}
    deps.update(pkg.get("dependencies", {}) or {})
    deps.update(pkg.get("devDependencies", {}) or {})
    for required in ("@capacitor/core", "@capacitor/cli", "@capacitor/device"):
        assert required in deps, (
            f"Expected '{required}' to be declared in dependencies or devDependencies of "
            f"{pkg_path}. Found keys: {sorted(deps)}"
        )


def test_capacitor_device_major_version_is_8():
    """The resolved version of @capacitor/device in node_modules must be major 8."""
    installed_pkg = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "device", "package.json"
    )
    assert os.path.isfile(installed_pkg), (
        f"Expected the @capacitor/device package to be installed at {installed_pkg}."
    )
    with open(installed_pkg) as f:
        data = json.load(f)
    version = str(data.get("version", ""))
    assert version, "@capacitor/device package.json has no 'version' field."
    major_str = version.split(".")[0]
    assert major_str.isdigit() and int(major_str) == 8, (
        "@capacitor/device installed version must have major === 8; "
        f"got {version!r}."
    )


def test_dist_index_html_exists():
    dist_index = os.path.join(PROJECT_DIR, "dist", "index.html")
    assert os.path.isfile(dist_index), (
        f"Expected production build output at {dist_index}. "
        "Make sure `npm run build` succeeded."
    )


def test_npm_run_build_succeeds():
    """Running `npm run build` again must exit 0 to keep the project buildable."""
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Expected `npm run build` to succeed.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert os.path.isfile(os.path.join(PROJECT_DIR, "dist", "index.html")), (
        "`npm run build` succeeded but dist/index.html is still missing."
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


def test_index_served_with_required_elements(preview_server):
    response = requests.get(preview_server, timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server} returned status {response.status_code}; expected 200."
    )
    body = response.text
    for marker in ("device-platform", "device-os-version", "device-lang", "lang-btn"):
        assert re.search(rf"id\s*=\s*[\"']{marker}[\"']", body), (
            f"The served index.html must contain an element with id=\"{marker}\". "
            f"Got body:\n{body[:1000]}"
        )


# ---------------------------------------------------------------------------
# Browser-driven behavioural verification
# ---------------------------------------------------------------------------


def test_device_info_and_language_rendered_in_browser(preview_server):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # Launch Chromium with English locale so the language code is deterministic.
        browser = p.chromium.launch(
            headless=True,
            args=["--lang=en-US"],
        )
        try:
            context = browser.new_context(locale="en-US")
            page = context.new_page()
            page.goto(preview_server, wait_until="load")

            page.wait_for_selector("#device-platform", state="attached", timeout=10_000)
            page.wait_for_selector(
                "#device-os-version", state="attached", timeout=10_000
            )
            page.wait_for_selector("#lang-btn", state="attached", timeout=10_000)
            page.wait_for_selector("#device-lang", state="attached", timeout=10_000)

            # Wait until #device-platform and #device-os-version are populated
            # (the executor sets them after awaiting Device.getInfo()).
            page.wait_for_function(
                "document.getElementById('device-platform') && "
                "document.getElementById('device-platform').textContent.trim().length > 0 && "
                "document.getElementById('device-os-version') && "
                "document.getElementById('device-os-version').textContent.trim().length > 0",
                timeout=15_000,
            )

            platform_text = page.evaluate(
                "document.getElementById('device-platform').textContent.trim()"
            )
            os_version_text = page.evaluate(
                "document.getElementById('device-os-version').textContent.trim()"
            )

            assert platform_text == "web", (
                "Expected #device-platform to display 'web' on the web target; "
                f"got {platform_text!r}."
            )

            assert os_version_text, (
                "Expected #device-os-version to display a non-empty version string; "
                "got an empty value."
            )
            assert re.match(r"^[0-9].*", os_version_text), (
                "Expected #device-os-version to match the regex '^[0-9].*' "
                f"(a version-like string starting with a digit); got {os_version_text!r}."
            )

            # The language span must be empty before the button is clicked. This
            # confirms the agent wired the value reactively rather than at load.
            initial_lang = page.evaluate(
                "document.getElementById('device-lang').textContent.trim()"
            )
            assert initial_lang == "", (
                "Expected #device-lang to be empty before clicking #lang-btn, "
                f"got {initial_lang!r}."
            )

            page.click("#lang-btn")

            page.wait_for_function(
                "document.getElementById('device-lang') && "
                "document.getElementById('device-lang').textContent.trim().length > 0",
                timeout=10_000,
            )

            lang_text = page.evaluate(
                "document.getElementById('device-lang').textContent.trim()"
            )
            assert re.match(r"^[a-z]{2}(-[A-Z]{2})?$", lang_text), (
                "Expected #device-lang to match the regex '^[a-z]{2}(-[A-Z]{2})?$' "
                f"after clicking #lang-btn; got {lang_text!r}."
            )
            assert "en" in lang_text, (
                "Expected #device-lang to contain 'en' (Chromium was launched with "
                f"--lang=en-US); got {lang_text!r}."
            )

            context.close()
        finally:
            browser.close()
