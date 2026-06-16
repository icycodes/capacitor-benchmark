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

ISO_TIMESTAMP_PATH_REGEX = re.compile(
    r"^photos/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z\.jpeg$"
)

# Two minimal but distinct valid JPEG byte sequences. Each starts with the
# JPEG SOI marker (FF D8), contains a JFIF APP0 segment with different
# version/density bytes, a single empty quantization table sized to a
# different length, and ends with the EOI marker (FF D9). The contents are
# intentionally crafted so the two fixtures are byte-distinct.

def _make_jpeg(seed_byte: int) -> bytes:
    return bytes([
        0xFF, 0xD8,                                           # SOI
        0xFF, 0xE0, 0x00, 0x10,                               # APP0 length=16
        0x4A, 0x46, 0x49, 0x46, 0x00,                         # "JFIF\0"
        0x01, 0x01,                                           # version
        0x00,                                                 # units
        0x00, 0x48, 0x00, 0x48,                               # X/Y density
        0x00, 0x00,                                           # thumbnail w/h
        0xFF, 0xDB, 0x00, 0x43, 0x00,                         # DQT segment
    ]) + bytes([seed_byte] * 64) + bytes([
        0xFF, 0xD9,                                           # EOI
    ])


FIXTURE_A_BYTES = _make_jpeg(0x10)
FIXTURE_B_BYTES = _make_jpeg(0x20)


# ---------------------------------------------------------------------------
# Static / config-level verification
# ---------------------------------------------------------------------------


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


def _parse_semver(version: str):
    # Strip any prerelease/build metadata.
    core = version.split("-")[0].split("+")[0]
    parts = core.split(".")
    return tuple(int(p) for p in parts[:3])


def test_capacitor_config_values():
    cfg, path = _read_capacitor_config()
    assert cfg.get("appName") == "Photo Gallery", (
        f"capacitor config at {path} must set appName to 'Photo Gallery'; "
        f"got {cfg.get('appName')!r}."
    )
    assert cfg.get("appId") == "com.example.photogallery", (
        f"capacitor config at {path} must set appId to 'com.example.photogallery'; "
        f"got {cfg.get('appId')!r}."
    )
    assert cfg.get("webDir") == "dist", (
        f"capacitor config at {path} must set webDir to 'dist'; got {cfg.get('webDir')!r}."
    )


def test_package_json_lists_required_dependencies():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), f"package.json not found at {pkg_path}."
    with open(pkg_path) as f:
        pkg = json.load(f)
    deps = {}
    deps.update(pkg.get("dependencies", {}) or {})
    deps.update(pkg.get("devDependencies", {}) or {})
    for required in (
        "@capacitor/core",
        "@capacitor/cli",
        "@capacitor/camera",
        "@capacitor/filesystem",
        "@capacitor/preferences",
    ):
        assert required in deps, (
            f"Expected '{required}' to be declared in dependencies or devDependencies of "
            f"{pkg_path}. Found keys: {sorted(deps)}"
        )


def test_capacitor_camera_installed_version_is_8_1_or_higher():
    camera_pkg = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "camera", "package.json"
    )
    assert os.path.isfile(camera_pkg), (
        f"Expected @capacitor/camera to be installed at {camera_pkg}. "
        "Run `npm install @capacitor/camera`."
    )
    with open(camera_pkg) as f:
        meta = json.load(f)
    version = meta.get("version", "0.0.0")
    parts = _parse_semver(version)
    assert parts >= (8, 1, 0), (
        f"Expected @capacitor/camera version >= 8.1.0 (which introduces `takePhoto`); "
        f"got {version!r}."
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
    for required_id in ("capture-btn", "capture-status"):
        assert re.search(rf"id\s*=\s*[\"']{re.escape(required_id)}[\"']", body), (
            f"The served index.html must contain an element with id=\"{required_id}\". "
            f"Got body (first 1000 chars):\n{body[:1000]}"
        )


# ---------------------------------------------------------------------------
# Browser-driven behavioural verification
# ---------------------------------------------------------------------------


def _text(page, selector: str) -> str:
    return page.evaluate(
        "(sel) => (document.querySelector(sel)?.textContent ?? '').trim()",
        selector,
    )


def _wait_for_status(page, expected: str, timeout_ms: int = 30_000):
    page.wait_for_function(
        "(want) => document.querySelector('#capture-status')?.textContent?.trim() === want",
        arg=expected,
        timeout=timeout_ms,
    )


def _list_photos(page):
    return page.evaluate("async () => await window.gallery.listPhotos()")


def _get_preferences_index_raw(page):
    """Capacitor Preferences web fallback stores values in localStorage with
    the default `CapacitorStorage.` group prefix. Read the raw stored string
    for the `photo_index` key."""
    return page.evaluate(
        "() => window.localStorage.getItem('CapacitorStorage.photo_index')"
    )


def _capture_with_fixture(page, tmp_path, fixture_name: str, fixture_bytes: bytes):
    file_path = tmp_path / fixture_name
    file_path.write_bytes(fixture_bytes)

    fc_holder = {}

    def _on_filechooser(fc):
        fc_holder["fc"] = fc
        fc.set_files(str(file_path))

    page.on("filechooser", _on_filechooser)
    try:
        page.click("#capture-btn")
        _wait_for_status(page, "saved")
    finally:
        page.remove_listener("filechooser", _on_filechooser)

    assert "fc" in fc_holder, (
        "Clicking #capture-btn must trigger a file picker dialog (the web "
        "fallback of Camera.takePhoto opens an <input type=file>)."
    )


def test_photo_gallery_full_flow(preview_server, tmp_path):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            # Fresh context => empty localStorage/IndexedDB by default.
            context = browser.new_context()
            page = context.new_page()
            page.goto(preview_server, wait_until="load")
            page.wait_for_selector("#capture-btn", state="visible", timeout=10_000)
            page.wait_for_selector("#capture-status", state="attached", timeout=10_000)
            # Give the entry script a brief moment to populate window.gallery.
            page.wait_for_function(
                "() => window.gallery && typeof window.gallery.capturePhoto === 'function'",
                timeout=10_000,
            )

            # --- Initial state ---
            assert _text(page, "#capture-status") == "idle", (
                "On first load, #capture-status must contain the text 'idle'; "
                f"got {_text(page, '#capture-status')!r}."
            )
            for name in ("capturePhoto", "listPhotos", "deletePhoto"):
                assert page.evaluate(
                    "(n) => typeof window.gallery[n] === 'function'", name
                ), f"window.gallery.{name} must be defined as a function on the page."

            initial_list = _list_photos(page)
            assert initial_list == [], (
                "Before any capture, window.gallery.listPhotos() must return []. "
                f"Got {initial_list!r}."
            )

            # --- First capture ---
            _capture_with_fixture(page, tmp_path, "fixture_a.jpg", FIXTURE_A_BYTES)
            list_after_first = _list_photos(page)
            assert isinstance(list_after_first, list) and len(list_after_first) == 1, (
                "After the first capture, listPhotos() must return an array of "
                f"length 1; got {list_after_first!r}."
            )
            first_path = list_after_first[0]
            assert ISO_TIMESTAMP_PATH_REGEX.match(first_path), (
                "The stored path must look like 'photos/<isoTimestamp>.jpeg'; "
                f"got {first_path!r}."
            )

            raw_after_first = _get_preferences_index_raw(page)
            assert raw_after_first is not None, (
                "The Capacitor Preferences key 'photo_index' must be set after the "
                "first capture (looked up via localStorage with the default "
                "'CapacitorStorage.' group prefix)."
            )
            parsed_after_first = json.loads(raw_after_first)
            assert parsed_after_first == list_after_first, (
                "The Preferences value at key 'photo_index' must equal the JSON "
                "serialisation of listPhotos(). "
                f"Got Preferences={raw_after_first!r} vs listPhotos={list_after_first!r}."
            )

            # --- Second capture (different fixture, distinct timestamp) ---
            # Add a small delay so the ISO timestamp differs from the first.
            page.wait_for_timeout(50)
            # Reset status text to allow waiting for the next 'saved' transition.
            page.evaluate(
                "() => { const el = document.querySelector('#capture-status'); if (el) el.textContent = 'idle'; }"
            )
            _capture_with_fixture(page, tmp_path, "fixture_b.jpg", FIXTURE_B_BYTES)
            list_after_second = _list_photos(page)
            assert isinstance(list_after_second, list) and len(list_after_second) == 2, (
                "After the second capture, listPhotos() must return an array of "
                f"length 2; got {list_after_second!r}."
            )
            assert list_after_second[0] == first_path, (
                "Insertion order must be preserved: the first stored path must remain "
                f"at index 0. Expected {first_path!r}; got {list_after_second[0]!r}."
            )
            second_path = list_after_second[1]
            assert ISO_TIMESTAMP_PATH_REGEX.match(second_path), (
                "The second stored path must also look like 'photos/<isoTimestamp>.jpeg'; "
                f"got {second_path!r}."
            )
            assert second_path != first_path, (
                "Two consecutive capturePhoto() calls must produce distinct stored "
                f"paths. Got identical paths {first_path!r}."
            )

            # --- Persistence across reload ---
            page.reload(wait_until="load")
            page.wait_for_selector("#capture-btn", state="visible", timeout=10_000)
            page.wait_for_function(
                "() => window.gallery && typeof window.gallery.listPhotos === 'function'",
                timeout=10_000,
            )
            assert _text(page, "#capture-status") == "idle", (
                "After a reload, #capture-status must reset to 'idle'; "
                f"got {_text(page, '#capture-status')!r}."
            )
            list_after_reload = _list_photos(page)
            assert list_after_reload == list_after_second, (
                "After a reload, listPhotos() must still return the previously "
                f"captured paths in the same order. Expected {list_after_second!r}; "
                f"got {list_after_reload!r}."
            )

            # --- Delete behaviour ---
            page.evaluate(
                "async (p) => { await window.gallery.deletePhoto(p); }",
                first_path,
            )
            list_after_delete = _list_photos(page)
            assert list_after_delete == [second_path], (
                "After deletePhoto(first_path), listPhotos() must return only the "
                f"second path. Expected {[second_path]!r}; got {list_after_delete!r}."
            )

            raw_after_delete = _get_preferences_index_raw(page)
            assert raw_after_delete is not None, (
                "Preferences key 'photo_index' must still exist after a delete."
            )
            parsed_after_delete = json.loads(raw_after_delete)
            assert parsed_after_delete == [second_path], (
                "Preferences 'photo_index' must equal a JSON array of just the "
                f"remaining path. Got {raw_after_delete!r}."
            )

            # --- Capture again after delete to prove integrity of the index ---
            page.wait_for_timeout(50)
            page.evaluate(
                "() => { const el = document.querySelector('#capture-status'); if (el) el.textContent = 'idle'; }"
            )
            _capture_with_fixture(page, tmp_path, "fixture_a2.jpg", FIXTURE_A_BYTES)
            list_after_recapture = _list_photos(page)
            assert isinstance(list_after_recapture, list) and len(list_after_recapture) == 2, (
                "After capturing again post-deletion, listPhotos() must contain 2 "
                f"entries; got {list_after_recapture!r}."
            )
            assert list_after_recapture[0] == second_path, (
                "Insertion order must be preserved: the surviving path must remain "
                f"at index 0. Expected {second_path!r}; got {list_after_recapture[0]!r}."
            )
            new_path = list_after_recapture[1]
            assert ISO_TIMESTAMP_PATH_REGEX.match(new_path), (
                "The newly captured path must match the ISO timestamp pattern; "
                f"got {new_path!r}."
            )
            assert new_path != first_path and new_path != second_path, (
                "The newly captured path must be distinct from any previous path."
            )

            context.close()
        finally:
            browser.close()
