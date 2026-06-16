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
# Truth Step 1: package.json declares @capacitor/dialog at major 8
# ---------------------------------------------------------------------------


def test_dialog_dependency_at_major_8():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), (
        f"Expected package.json at {pkg_path} after the task completes."
    )
    with open(pkg_path) as f:
        data = json.load(f)
    deps = data.get("dependencies") or {}
    assert isinstance(deps, dict), "package.json 'dependencies' must be an object."
    assert "@capacitor/dialog" in deps, (
        "Expected '@capacitor/dialog' to be declared in package.json "
        "'dependencies' after the task completes; got dependencies="
        f"{sorted(deps.keys())}."
    )

    installed_pkg_path = os.path.join(
        PROJECT_DIR,
        "node_modules",
        "@capacitor",
        "dialog",
        "package.json",
    )
    if os.path.isfile(installed_pkg_path):
        with open(installed_pkg_path) as f:
            installed = json.load(f)
        installed_version = installed.get("version")
        resolved_major = _semver_major(installed_version)
        assert resolved_major == 8, (
            "Expected the installed '@capacitor/dialog' to be at major version 8, "
            f"but {installed_pkg_path} reports version={installed_version!r}."
        )
    else:
        spec_major = _semver_major(deps["@capacitor/dialog"])
        assert spec_major == 8, (
            "Expected package.json to pin '@capacitor/dialog' to a v8 specifier; "
            f"got {deps['@capacitor/dialog']!r}."
        )


# ---------------------------------------------------------------------------
# Truth Step 2: `npm run build` succeeds and produces dist/index.html
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


# ---------------------------------------------------------------------------
# Truth Step 3: `npx cap sync` succeeds
# ---------------------------------------------------------------------------


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
# Vite preview fixture (shared by HTTP & Playwright tests)
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
        timeout = 180
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex((PREVIEW_HOST, PREVIEW_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)
    yield PREVIEW_URL
    info = xprocess.getinfo(Starter.name)
    info.terminate()


# ---------------------------------------------------------------------------
# Truth Step 4: HTTP 200 from preview
# ---------------------------------------------------------------------------


def test_preview_serves_html_200(preview_server):
    response = requests.get(preview_server, timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server} returned status {response.status_code}; expected 200."
    )


# ---------------------------------------------------------------------------
# Truth Steps 5 & 6: Playwright Chromium with `add_init_script` overrides
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def playwright_browser(preview_server):
    """Launch a single headless Chromium and reuse it across the two tests."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        try:
            yield browser
        finally:
            browser.close()


def _run_prompt_scenario(browser, init_script, expected_text):
    """
    Open a fresh browser context, inject `init_script` BEFORE the page loads
    (so it runs before any module code), click `#prompt-btn`, and wait for
    `#prompt-result.textContent === expected_text`.
    """
    context = browser.new_context()
    try:
        context.add_init_script(init_script)
        page = context.new_page()
        page.goto(PREVIEW_URL, wait_until="load", timeout=20000)

        # Wait for the wiring to land in the DOM before clicking.
        page.wait_for_selector("#prompt-btn", state="attached", timeout=10000)
        page.wait_for_selector("#prompt-result", state="attached", timeout=10000)

        page.click("#prompt-btn")

        # Wait up to 10s for #prompt-result.textContent to match exactly.
        page.wait_for_function(
            """expected => {
                const el = document.querySelector('#prompt-result');
                return el && el.textContent === expected;
            }""",
            arg=expected_text,
            timeout=10000,
        )

        actual = page.eval_on_selector(
            "#prompt-result", "el => el.textContent"
        )
        assert actual == expected_text, (
            f"Expected #prompt-result.textContent to be {expected_text!r}, "
            f"got {actual!r}."
        )
    finally:
        context.close()


def test_prompt_accepted_value_renders_pochi(playwright_browser):
    """Truth Step 5: window.prompt → "Pochi" => #prompt-result === "Pochi"."""
    _run_prompt_scenario(
        playwright_browser,
        init_script='window.prompt = (msg) => "Pochi";',
        expected_text="Pochi",
    )


def test_prompt_cancelled_renders_literal_cancelled(playwright_browser):
    """Truth Step 6: window.prompt → null => #prompt-result === "cancelled"."""
    _run_prompt_scenario(
        playwright_browser,
        init_script="window.prompt = () => null;",
        expected_text="cancelled",
    )
