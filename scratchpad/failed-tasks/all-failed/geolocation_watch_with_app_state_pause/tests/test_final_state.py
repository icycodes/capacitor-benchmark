import json
import os
import re
import shutil
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

REQUIRED_PLUGINS = ("@capacitor/app", "@capacitor/geolocation", "@capacitor/preferences")


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
# Truth Step 1: package.json declares all three plugins at major 8
# ---------------------------------------------------------------------------


def test_required_plugins_declared_at_major_8():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), (
        f"Expected package.json at {pkg_path} after the task completes."
    )
    with open(pkg_path) as f:
        data = json.load(f)
    deps = data.get("dependencies") or {}
    assert isinstance(deps, dict), "package.json 'dependencies' must be an object."

    for plugin in REQUIRED_PLUGINS:
        assert plugin in deps, (
            f"Expected '{plugin}' to be declared under 'dependencies' in package.json "
            f"after the task completes; got dependency keys: {sorted(deps.keys())}."
        )

        installed_pkg = os.path.join(
            PROJECT_DIR,
            "node_modules",
            "@capacitor",
            plugin.split("/", 1)[1],
            "package.json",
        )
        resolved_major = None
        resolved_version = None
        if os.path.isfile(installed_pkg):
            with open(installed_pkg) as f:
                installed = json.load(f)
            resolved_version = installed.get("version")
            resolved_major = _semver_major(resolved_version)
        else:
            resolved_version = deps[plugin]
            resolved_major = _semver_major(resolved_version)

        assert resolved_major == 8, (
            f"Expected the installed '{plugin}' to be at major version 8, "
            f"got version={resolved_version!r}."
        )


# ---------------------------------------------------------------------------
# Truth Steps 2 & 3: npm run build + npx cap sync
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
# Truth Step 4 + 5: preview HTTP 200 + browser-driven behavioural verification
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
    yield PREVIEW_URL
    info = xprocess.getinfo(Starter.name)
    info.terminate()


def test_preview_serves_html(preview_server):
    response = requests.get(preview_server, timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server} returned status {response.status_code}; expected 200."
    )


# ---------------------------------------------------------------------------
# Browser-driven scenarios
# ---------------------------------------------------------------------------

MOCK_GEO_INIT_SCRIPT = """
(() => {
  let nextId = 1;
  const watches = new Map();
  Object.defineProperty(navigator, 'geolocation', {
    configurable: true,
    value: {
      watchPosition: (success, error, options) => {
        const id = nextId++;
        watches.set(id, { success, error, options });
        return id;
      },
      clearWatch: (id) => { watches.delete(id); },
      getCurrentPosition: (success, error, options) => {},
    },
  });
  window.__mockGeo = {
    activeWatchCount: () => watches.size,
    activeWatchIds: () => Array.from(watches.keys()),
    emit: (lat, lng, timestamp) => {
      const pos = {
        coords: {
          latitude: lat,
          longitude: lng,
          accuracy: 5,
          altitude: null,
          altitudeAccuracy: null,
          heading: null,
          speed: null,
        },
        timestamp,
      };
      for (const w of Array.from(watches.values())) {
        w.success(pos);
      }
    },
  };
})();
"""

HIDE_VISIBILITY_JS = (
    "Object.defineProperty(document, 'hidden', { value: true, configurable: true });"
    " Object.defineProperty(document, 'visibilityState', { value: 'hidden', configurable: true });"
    " document.dispatchEvent(new Event('visibilitychange'));"
)

SHOW_VISIBILITY_JS = (
    "Object.defineProperty(document, 'hidden', { value: false, configurable: true });"
    " Object.defineProperty(document, 'visibilityState', { value: 'visible', configurable: true });"
    " document.dispatchEvent(new Event('visibilitychange'));"
)


def _poll(fn, predicate, timeout_s=3.0, interval_s=0.05):
    """Repeatedly evaluate `fn` until `predicate(value)` returns True or timeout."""
    deadline = time.monotonic() + timeout_s
    last = None
    while time.monotonic() < deadline:
        try:
            last = fn()
        except Exception:
            last = None
        if predicate(last):
            return last, True
        time.sleep(interval_s)
    return last, False


def _wait_for_tracker(page, timeout_ms=5000):
    """Wait until window.tracker (with start/stop/getLatest) is available."""
    page.wait_for_function(
        """
        () => {
          const t = window.tracker;
          return !!t
            && typeof t.start === 'function'
            && typeof t.stop === 'function'
            && typeof t.getLatest === 'function';
        }
        """,
        timeout=timeout_ms,
    )


def _get_latest(page):
    return page.evaluate(
        "async () => { const v = await window.tracker.getLatest(); return v; }"
    )


def _active_watches(page) -> int:
    return page.evaluate("() => window.__mockGeo.activeWatchCount()")


def test_tracker_end_to_end(preview_server):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        try:
            context = browser.new_context()
            # Install the geolocation mock BEFORE any page script evaluates.
            context.add_init_script(MOCK_GEO_INIT_SCRIPT)
            page = context.new_page()

            # --- Scenario (a): initial cold state ---
            page.goto(preview_server, wait_until="load", timeout=30000)
            _wait_for_tracker(page, timeout_ms=10000)

            initial = _get_latest(page)
            assert initial is None, (
                "Before start() and with empty localStorage, window.tracker.getLatest() "
                f"must resolve to null; got {initial!r}."
            )

            # --- Scenario (b): start registers exactly one watch ---
            page.evaluate("async () => { await window.tracker.start(); }")
            count, ok = _poll(lambda: _active_watches(page), lambda v: v == 1, timeout_s=3.0)
            assert ok, (
                "After window.tracker.start(), exactly one geolocation watch must be active; "
                f"observed activeWatchCount={count!r}."
            )

            # --- Scenario (c): first position ---
            page.evaluate(
                "() => window.__mockGeo.emit(37.5, -122.5, 1700000001000)"
            )
            latest, ok = _poll(
                lambda: _get_latest(page),
                lambda v: isinstance(v, dict)
                and v.get("timestamp") == 1700000001000,
                timeout_s=3.0,
            )
            assert ok, (
                "After emitting (37.5, -122.5, 1700000001000), getLatest() must return an "
                "object with that timestamp; last observed: "
                f"{latest!r}."
            )
            assert isinstance(latest, dict), "getLatest() must resolve to an object."
            assert latest.get("lat") == 37.5, (
                f"Expected getLatest().lat == 37.5; got {latest!r}."
            )
            assert latest.get("lng") == -122.5, (
                f"Expected getLatest().lng == -122.5; got {latest!r}."
            )
            assert latest.get("timestamp") == 1700000001000, (
                f"Expected getLatest().timestamp == 1700000001000; got {latest!r}."
            )

            # --- Scenario (d): second position ---
            page.evaluate(
                "() => window.__mockGeo.emit(38.25, -121.75, 1700000002000)"
            )
            latest, ok = _poll(
                lambda: _get_latest(page),
                lambda v: isinstance(v, dict)
                and v.get("timestamp") == 1700000002000,
                timeout_s=3.0,
            )
            assert ok, (
                "After emitting (38.25, -121.75, 1700000002000), getLatest() must return "
                f"that position; last observed: {latest!r}."
            )
            assert latest == {"lat": 38.25, "lng": -121.75, "timestamp": 1700000002000}, (
                "Expected getLatest() to deep-equal {lat:38.25,lng:-121.75,timestamp:1700000002000}; "
                f"got {latest!r}."
            )

            # --- Scenario (e): persistence (CapacitorStorage.last_position) ---
            stored_raw, ok = _poll(
                lambda: page.evaluate(
                    "() => window.localStorage.getItem('CapacitorStorage.last_position')"
                ),
                lambda v: isinstance(v, str) and v.strip() != "",
                timeout_s=3.0,
            )
            assert ok, (
                "After a position update, localStorage['CapacitorStorage.last_position'] "
                f"must be a non-empty string; got {stored_raw!r}."
            )
            try:
                stored_value = json.loads(stored_raw)
            except (json.JSONDecodeError, TypeError) as exc:
                pytest.fail(
                    "Expected CapacitorStorage.last_position to be a JSON-serialised "
                    f"position object; got {stored_raw!r} ({exc})."
                )

            def _has_numeric(container, expected: float) -> bool:
                if isinstance(container, dict):
                    return any(_has_numeric(v, expected) for v in container.values())
                if isinstance(container, list):
                    return any(_has_numeric(v, expected) for v in container)
                if isinstance(container, (int, float)):
                    return float(container) == float(expected)
                return False

            for expected_number in (38.25, -121.75, 1700000002000):
                assert _has_numeric(stored_value, expected_number), (
                    "Expected the persisted last_position JSON to contain the value "
                    f"{expected_number}; got {stored_value!r}."
                )

            # --- Scenario (f): background pause ---
            page.evaluate(f"() => {{ {HIDE_VISIBILITY_JS} }}")
            count, ok = _poll(
                lambda: _active_watches(page), lambda v: v == 0, timeout_s=3.0
            )
            assert ok, (
                "After dispatching visibilitychange with document.hidden=true, the "
                "geolocation watch must be cleared (activeWatchCount==0); last observed: "
                f"{count!r}."
            )

            # --- Scenario (g): emit while background does not update getLatest ---
            page.evaluate("() => window.__mockGeo.emit(50.0, 50.0, 1700000003000)")
            time.sleep(0.3)
            latest = _get_latest(page)
            assert latest == {"lat": 38.25, "lng": -121.75, "timestamp": 1700000002000}, (
                "While in background, additional emitted positions must NOT update "
                "getLatest(); expected the pre-background value "
                "{lat:38.25,lng:-121.75,timestamp:1700000002000} but observed "
                f"{latest!r}."
            )

            # --- Scenario (h): foreground resume ---
            page.evaluate(f"() => {{ {SHOW_VISIBILITY_JS} }}")
            count, ok = _poll(
                lambda: _active_watches(page), lambda v: v == 1, timeout_s=3.0
            )
            assert ok, (
                "After dispatching visibilitychange with document.hidden=false, a new "
                "geolocation watch must be registered (activeWatchCount==1); last "
                f"observed: {count!r}."
            )

            # --- Scenario (i): position after resume ---
            page.evaluate(
                "() => window.__mockGeo.emit(40.5, -119.5, 1700000004000)"
            )
            latest, ok = _poll(
                lambda: _get_latest(page),
                lambda v: isinstance(v, dict)
                and v.get("timestamp") == 1700000004000,
                timeout_s=3.0,
            )
            assert ok, (
                "After foreground resume, emitting (40.5, -119.5, 1700000004000) must "
                f"update getLatest(); last observed: {latest!r}."
            )
            assert latest == {"lat": 40.5, "lng": -119.5, "timestamp": 1700000004000}, (
                "Expected getLatest() after resume to deep-equal "
                "{lat:40.5,lng:-119.5,timestamp:1700000004000}; "
                f"got {latest!r}."
            )

            # --- Scenario (j): cold start via reload ---
            page.reload(wait_until="load", timeout=30000)
            _wait_for_tracker(page, timeout_ms=10000)
            cold, ok = _poll(
                lambda: _get_latest(page),
                lambda v: isinstance(v, dict)
                and v.get("timestamp") == 1700000004000,
                timeout_s=5.0,
            )
            assert ok, (
                "On cold start (after page.reload, BEFORE start()), getLatest() must "
                "resolve to the previously persisted position "
                "{lat:40.5,lng:-119.5,timestamp:1700000004000}; "
                f"last observed: {cold!r}."
            )
            assert cold == {"lat": 40.5, "lng": -119.5, "timestamp": 1700000004000}, (
                "Cold-start getLatest() must deep-equal the previously persisted "
                "{lat:40.5,lng:-119.5,timestamp:1700000004000}; "
                f"got {cold!r}."
            )

            # --- Scenario (k): restart after reload ---
            page.evaluate("async () => { await window.tracker.start(); }")
            count, ok = _poll(
                lambda: _active_watches(page), lambda v: v == 1, timeout_s=3.0
            )
            assert ok, (
                "After window.tracker.start() following a reload, exactly one "
                f"geolocation watch must be active; observed activeWatchCount={count!r}."
            )

            # --- Scenario (l): stop removes the watch ---
            page.evaluate("async () => { await window.tracker.stop(); }")
            count, ok = _poll(
                lambda: _active_watches(page), lambda v: v == 0, timeout_s=3.0
            )
            assert ok, (
                "After window.tracker.stop(), no geolocation watches must remain "
                f"registered; observed activeWatchCount={count!r}."
            )

            # --- Scenario (m): stopped tracker ignores app state changes ---
            page.evaluate(f"() => {{ {HIDE_VISIBILITY_JS} }}")
            time.sleep(0.2)
            page.evaluate(f"() => {{ {SHOW_VISIBILITY_JS} }}")
            time.sleep(0.2)
            count = _active_watches(page)
            assert count == 0, (
                "After stop(), subsequent visibilitychange transitions must NOT register "
                f"a new geolocation watch; observed activeWatchCount={count!r}."
            )
        finally:
            browser.close()
