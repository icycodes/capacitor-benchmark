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
FIXTURE_HOST = "127.0.0.1"
FIXTURE_PORT = 4174
FIXTURE_URL = f"http://{FIXTURE_HOST}:{FIXTURE_PORT}"
FIXTURE_DATA_URL = f"{FIXTURE_URL}/api/data"
FIXTURE_SCRIPT = "/opt/fixtures/etag_server.js"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_capacitor_config():
    """Return a (config_dict, source_path) tuple regardless of TS/JS/JSON format."""
    ts_path = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    js_path = os.path.join(PROJECT_DIR, "capacitor.config.js")
    json_path = os.path.join(PROJECT_DIR, "capacitor.config.json")

    if os.path.isfile(json_path):
        with open(json_path) as f:
            return json.load(f), json_path, ""

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
        return cfg, src_path, content

    raise AssertionError(
        "No Capacitor config file (capacitor.config.ts/js/json) found at the project root."
    )


def _read_offline_cache_module():
    path = os.path.join(PROJECT_DIR, "src", "cache", "offlineCache.ts")
    assert os.path.isfile(path), (
        f"Expected the offline cache module at {path}. The executor must create it."
    )
    with open(path) as f:
        return f.read(), path


def _stats():
    response = requests.get(f"{FIXTURE_URL}/api/control/stats", timeout=10)
    assert response.status_code == 200, (
        f"GET {FIXTURE_URL}/api/control/stats returned {response.status_code}: {response.text}"
    )
    return response.json()


def _reset_stats():
    response = requests.post(f"{FIXTURE_URL}/api/control/reset", timeout=10)
    assert response.status_code == 200, (
        f"POST {FIXTURE_URL}/api/control/reset returned {response.status_code}: {response.text}"
    )


def _rotate_payload():
    response = requests.post(f"{FIXTURE_URL}/api/control/rotate", timeout=10)
    assert response.status_code == 200, (
        f"POST {FIXTURE_URL}/api/control/rotate returned {response.status_code}: {response.text}"
    )
    return response.json()


# ---------------------------------------------------------------------------
# Static / config-level verification
# ---------------------------------------------------------------------------


def test_capacitor_config_values():
    cfg, path, raw_content = _read_capacitor_config()
    assert cfg.get("appName") == "Offline Cache Demo", (
        f"capacitor config at {path} must set appName to 'Offline Cache Demo'; "
        f"got {cfg.get('appName')!r}."
    )
    assert cfg.get("appId") == "com.example.offlinecache", (
        f"capacitor config at {path} must set appId to 'com.example.offlinecache'; "
        f"got {cfg.get('appId')!r}."
    )
    assert cfg.get("webDir") == "dist", (
        f"capacitor config at {path} must set webDir to 'dist'; got {cfg.get('webDir')!r}."
    )


def test_capacitor_http_plugin_enabled():
    cfg, path, raw_content = _read_capacitor_config()
    if path.endswith(".json"):
        plugins = cfg.get("plugins") or {}
        http_cfg = plugins.get("CapacitorHttp") or {}
        assert http_cfg.get("enabled") is True, (
            f"capacitor.config.json at {path} must set plugins.CapacitorHttp.enabled = true; "
            f"got plugins.CapacitorHttp = {http_cfg!r}."
        )
    else:
        # For TS/JS configs do a tolerant textual search: CapacitorHttp ... enabled ... true.
        assert re.search(
            r"CapacitorHttp[^}]*enabled\s*:\s*true",
            raw_content,
            flags=re.DOTALL,
        ), (
            f"capacitor config at {path} must enable the CapacitorHttp plugin "
            "(plugins.CapacitorHttp.enabled = true)."
        )


def test_package_json_lists_capacitor_dependencies():
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
        "@capacitor/filesystem",
        "@capacitor/preferences",
    ):
        assert required in deps, (
            f"Expected '{required}' to be declared in dependencies or devDependencies of "
            f"{pkg_path}. Found keys: {sorted(deps)}"
        )


def test_offline_cache_module_uses_capacitor_apis():
    source, path = _read_offline_cache_module()
    for token in ("CapacitorHttp", "Filesystem", "Preferences"):
        assert token in source, (
            f"{path} must reference '{token}' so that the module is implemented in "
            "terms of the Capacitor v8 APIs."
        )


def test_offline_cache_module_exports_required_functions():
    source, path = _read_offline_cache_module()
    for fn in ("getCached", "invalidate"):
        assert re.search(rf"export\s+(async\s+)?function\s+{fn}\b", source) or re.search(
            rf"export\s+(const|let)\s+{fn}\b", source
        ) or re.search(rf"export\s*{{[^}}]*\b{fn}\b[^}}]*}}", source), (
            f"{path} must export an async function or const named '{fn}'."
        )


def test_offline_cache_module_does_not_use_forbidden_http_clients():
    source, path = _read_offline_cache_module()
    # Strip line and block comments so we only inspect executable code.
    no_block = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    no_comments = re.sub(r"//[^\n]*", "", no_block)
    forbidden_patterns = [
        (r"\bwindow\.fetch\b", "window.fetch"),
        (r"\bXMLHttpRequest\b", "XMLHttpRequest"),
        (r"\baxios\b", "axios"),
    ]
    for pattern, label in forbidden_patterns:
        assert not re.search(pattern, no_comments), (
            f"{path} must not call '{label}' — all HTTP requests must go through CapacitorHttp."
        )
    # Standalone `fetch(` calls (not as a property like `CapacitorHttp.fetch`) are also
    # forbidden. We allow `Filesystem.readFile` etc, so use a negative-lookbehind.
    standalone_fetch = re.findall(r"(?<![\w.])fetch\s*\(", no_comments)
    assert not standalone_fetch, (
        f"{path} must not call the global fetch() — all HTTP requests must go through CapacitorHttp."
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
# Long-running services
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def fixture_server(xprocess):
    class Starter(ProcessStarter):
        name = "etag_fixture"
        args = ["node", FIXTURE_SCRIPT, "--port", str(FIXTURE_PORT)]
        env = os.environ.copy()
        popen_kwargs = {
            "cwd": "/tmp",
            "text": True,
        }
        timeout = 60
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((FIXTURE_HOST, FIXTURE_PORT)) != 0:
                    return False
            try:
                r = requests.get(f"{FIXTURE_URL}/api/control/stats", timeout=2)
                return r.status_code == 200
            except Exception:
                return False

    xprocess.ensure(Starter.name, Starter)
    yield FIXTURE_URL
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
    time.sleep(1.0)
    yield PREVIEW_URL
    info = xprocess.getinfo(Starter.name)
    info.terminate()


# ---------------------------------------------------------------------------
# Static page-level verification
# ---------------------------------------------------------------------------


def test_index_served_with_required_elements(preview_server):
    response = requests.get(preview_server, timeout=30)
    assert response.status_code == 200, (
        f"GET {preview_server} returned status {response.status_code}; expected 200."
    )
    body = response.text
    for required_id in (
        "url-input",
        "fetch-button",
        "invalidate-button",
        "status",
        "data",
        "source",
        "meta-etag",
        "meta-fetched-at",
    ):
        assert re.search(rf"id\s*=\s*[\"']{re.escape(required_id)}[\"']", body), (
            f"The served index.html must contain an element with id=\"{required_id}\". "
            f"Got body (first 1000 chars):\n{body[:1000]}"
        )


def test_fixture_server_responds(fixture_server):
    stats = _stats()
    for key in (
        "total",
        "last200",
        "last304",
        "lastIfNoneMatch",
        "currentEtag",
        "currentBody",
    ):
        assert key in stats, (
            f"Fixture server stats payload must include '{key}'. Got: {stats!r}"
        )


# ---------------------------------------------------------------------------
# Browser-driven behavioural verification
# ---------------------------------------------------------------------------


def _wait_for_status(page, expected: str, timeout_ms: int = 20_000):
    page.wait_for_function(
        "(want) => document.querySelector('#status')?.textContent?.trim() === want",
        arg=expected,
        timeout=timeout_ms,
    )


def _text(page, selector: str) -> str:
    return page.evaluate(
        "(sel) => (document.querySelector(sel)?.textContent ?? '').trim()",
        selector,
    )


def _set_url_input(page, url: str):
    page.evaluate(
        "(u) => { const el = document.querySelector('#url-input'); el.value = u; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }",
        url,
    )


def test_offline_cache_end_to_end(fixture_server, preview_server):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            page = context.new_page()
            page.goto(preview_server, wait_until="load")
            page.wait_for_selector("#fetch-button", state="visible", timeout=10_000)
            page.wait_for_selector(
                "#invalidate-button", state="visible", timeout=10_000
            )
            page.wait_for_selector("#url-input", state="visible", timeout=10_000)
            page.wait_for_timeout(300)

            # --- Initial UI state -------------------------------------------------
            assert _text(page, "#status") == "idle", (
                f"On first load, #status must contain the text 'idle'; got {_text(page, '#status')!r}."
            )
            for selector in ("#data", "#source", "#meta-etag", "#meta-fetched-at"):
                assert _text(page, selector) == "", (
                    f"On first load, {selector} must be empty; got {_text(page, selector)!r}."
                )

            # --- First fetch (network) -------------------------------------------
            _reset_stats()
            stats0 = _stats()
            etag_v1 = stats0["currentEtag"]
            body_v1 = stats0["currentBody"]
            assert isinstance(etag_v1, str) and etag_v1, (
                f"Fixture server must expose a non-empty currentEtag; got {etag_v1!r}."
            )
            body_v1_serialised = json.dumps(body_v1)

            _set_url_input(page, FIXTURE_DATA_URL)
            page.click("#fetch-button")
            _wait_for_status(page, "success")

            assert _text(page, "#source") == "network", (
                "First fetch must mark #source as 'network'; got "
                f"{_text(page, '#source')!r}."
            )
            assert _text(page, "#data") == body_v1_serialised, (
                "First fetch must render the fixture body via JSON.stringify; got "
                f"{_text(page, '#data')!r}, expected {body_v1_serialised!r}."
            )
            assert _text(page, "#meta-etag") == etag_v1, (
                "First fetch must populate #meta-etag with the fixture's ETag "
                f"({etag_v1!r}); got {_text(page, '#meta-etag')!r}."
            )
            assert re.fullmatch(r"\d+", _text(page, "#meta-fetched-at")), (
                "First fetch must populate #meta-fetched-at with a decimal millisecond "
                f"timestamp; got {_text(page, '#meta-fetched-at')!r}."
            )

            stats1 = _stats()
            assert stats1["total"] == 1, (
                f"After the first fetch, fixture total requests must be 1; got {stats1['total']}. Stats: {stats1}"
            )
            assert stats1["last200"] == 1 and stats1["last304"] == 0, (
                f"After the first fetch, last200/last304 must be 1/0; got {stats1['last200']}/{stats1['last304']}."
            )
            assert stats1["lastIfNoneMatch"] in (None, ""), (
                "First fetch must not include an If-None-Match header; "
                f"got lastIfNoneMatch={stats1['lastIfNoneMatch']!r}."
            )

            # --- Second fetch (304 cache) ----------------------------------------
            page.click("#fetch-button")
            _wait_for_status(page, "success")

            assert _text(page, "#source") == "cache", (
                "Second fetch (304 path) must mark #source as 'cache'; got "
                f"{_text(page, '#source')!r}."
            )
            assert _text(page, "#data") == body_v1_serialised, (
                "Second fetch must still render the same body; got "
                f"{_text(page, '#data')!r}, expected {body_v1_serialised!r}."
            )
            assert _text(page, "#meta-etag") == etag_v1, (
                "Second fetch must leave the stored ETag unchanged; got "
                f"{_text(page, '#meta-etag')!r}."
            )

            stats2 = _stats()
            assert stats2["total"] == 2, (
                f"After the second fetch, fixture total requests must be 2; got {stats2['total']}."
            )
            assert stats2["last304"] == 1, (
                "Second fetch must result in one 304 response; got "
                f"last304={stats2['last304']}."
            )
            assert stats2["lastIfNoneMatch"] == etag_v1, (
                "Second fetch must include If-None-Match equal to the stored ETag "
                f"({etag_v1!r}); got {stats2['lastIfNoneMatch']!r}."
            )

            # --- Persisted state via Preferences + Filesystem --------------------
            persisted = page.evaluate(
                """
                async () => {
                  const [{ Preferences }, { Filesystem, Directory, Encoding }] = await Promise.all([
                    import('@capacitor/preferences'),
                    import('@capacitor/filesystem'),
                  ]);
                  const meta = await Preferences.get({ key: 'cache_meta:demo' });
                  let file = null;
                  try {
                    const res = await Filesystem.readFile({
                      path: 'cache/demo.json',
                      directory: Directory.Cache,
                      encoding: Encoding.UTF8,
                    });
                    file = typeof res.data === 'string' ? res.data : await res.data.text();
                  } catch (e) {
                    file = null;
                  }
                  return { meta: meta.value, file };
                }
                """
            )
            assert persisted["meta"] is not None, (
                "Preferences must contain a value under 'cache_meta:demo' after a "
                "successful getCached call."
            )
            meta_obj = json.loads(persisted["meta"])
            assert meta_obj.get("etag") == etag_v1, (
                f"Stored metadata etag must equal {etag_v1!r}; got {meta_obj.get('etag')!r}."
            )
            assert (
                isinstance(meta_obj.get("fetchedAt"), (int, float))
                and meta_obj["fetchedAt"] > 0
            ), (
                "Stored metadata fetchedAt must be a positive number; got "
                f"{meta_obj.get('fetchedAt')!r}."
            )
            assert persisted["file"] is not None, (
                "Filesystem must contain a cache/demo.json file under Directory.Cache "
                "after a successful getCached call."
            )
            assert json.loads(persisted["file"]) == body_v1, (
                "The persisted on-disk JSON must equal the fixture's body. Got: "
                f"{persisted['file']!r}."
            )

            # --- Invalidate ------------------------------------------------------
            page.click("#invalidate-button")
            _wait_for_status(page, "invalidated")
            for selector in ("#data", "#source", "#meta-etag", "#meta-fetched-at"):
                assert _text(page, selector) == "", (
                    f"After invalidate, {selector} must be empty; got {_text(page, selector)!r}."
                )

            cleaned = page.evaluate(
                """
                async () => {
                  const [{ Preferences }, { Filesystem, Directory, Encoding }] = await Promise.all([
                    import('@capacitor/preferences'),
                    import('@capacitor/filesystem'),
                  ]);
                  const meta = await Preferences.get({ key: 'cache_meta:demo' });
                  let file = null;
                  try {
                    const res = await Filesystem.readFile({
                      path: 'cache/demo.json',
                      directory: Directory.Cache,
                      encoding: Encoding.UTF8,
                    });
                    file = typeof res.data === 'string' ? res.data : await res.data.text();
                  } catch (e) {
                    file = null;
                  }
                  return { meta: meta.value, file };
                }
                """
            )
            assert cleaned["meta"] is None, (
                "After invalidate, Preferences value for 'cache_meta:demo' must be null; "
                f"got {cleaned['meta']!r}."
            )
            assert cleaned["file"] is None, (
                "After invalidate, the cache/demo.json file must be gone; got "
                f"{cleaned['file']!r}."
            )

            # --- Re-fetch after invalidate (network) -----------------------------
            _reset_stats()
            page.click("#fetch-button")
            _wait_for_status(page, "success")
            assert _text(page, "#source") == "network", (
                "Re-fetch after invalidate must mark #source as 'network'; got "
                f"{_text(page, '#source')!r}."
            )
            assert _text(page, "#data") == body_v1_serialised, (
                "Re-fetch after invalidate must render the current fixture body; got "
                f"{_text(page, '#data')!r}."
            )
            assert _text(page, "#meta-etag") == etag_v1, (
                "Re-fetch after invalidate must store the current ETag; got "
                f"{_text(page, '#meta-etag')!r}."
            )

            stats3 = _stats()
            assert stats3["total"] == 1, (
                "Re-fetch after invalidate must trigger exactly one new request; "
                f"got total={stats3['total']}."
            )
            assert stats3["last200"] == 1, (
                f"Re-fetch after invalidate must produce a 200; got last200={stats3['last200']}."
            )
            assert stats3["lastIfNoneMatch"] in (None, ""), (
                "Re-fetch after invalidate must not include If-None-Match; got "
                f"{stats3['lastIfNoneMatch']!r}."
            )

            # --- Server-side payload rotation ------------------------------------
            rotated = _rotate_payload()
            etag_v2 = rotated["etag"]
            body_v2 = rotated["body"]
            assert etag_v2 != etag_v1, (
                f"Rotated ETag must differ from the original; got {etag_v2!r}."
            )
            assert body_v2 != body_v1, (
                f"Rotated body must differ from the original; got {body_v2!r}."
            )
            body_v2_serialised = json.dumps(body_v2)

            _reset_stats()
            page.click("#fetch-button")
            _wait_for_status(page, "success")
            assert _text(page, "#source") == "network", (
                "After server rotation, the next fetch must hit the network; got #source="
                f"{_text(page, '#source')!r}."
            )
            assert _text(page, "#data") == body_v2_serialised, (
                "After server rotation, #data must reflect the new body; got "
                f"{_text(page, '#data')!r}."
            )
            assert _text(page, "#meta-etag") == etag_v2, (
                "After server rotation, #meta-etag must equal the new ETag; got "
                f"{_text(page, '#meta-etag')!r}."
            )

            stats4 = _stats()
            assert stats4["total"] == 1, (
                f"Post-rotation fetch must trigger exactly one new request; got total={stats4['total']}."
            )
            assert stats4["last200"] == 1 and stats4["last304"] == 0, (
                "Post-rotation fetch must produce a 200 (server returned new content); got "
                f"last200/last304={stats4['last200']}/{stats4['last304']}."
            )
            assert stats4["lastIfNoneMatch"] == etag_v1, (
                "Post-rotation fetch must send the previously stored ETag; got "
                f"{stats4['lastIfNoneMatch']!r}, expected {etag_v1!r}."
            )

            page.click("#fetch-button")
            _wait_for_status(page, "success")
            assert _text(page, "#source") == "cache", (
                "After rotation, the second fetch must hit the cache via 304; got #source="
                f"{_text(page, '#source')!r}."
            )
            assert _text(page, "#meta-etag") == etag_v2, (
                "After rotation, #meta-etag must still equal the new ETag; got "
                f"{_text(page, '#meta-etag')!r}."
            )

            stats5 = _stats()
            assert stats5["total"] == 2, (
                f"After rotation, two requests must have been observed; got total={stats5['total']}."
            )
            assert stats5["last304"] == 1, (
                f"After rotation, exactly one 304 must have been recorded; got last304={stats5['last304']}."
            )
            assert stats5["lastIfNoneMatch"] == etag_v2, (
                "After rotation, the last If-None-Match header must equal the new ETag; "
                f"got {stats5['lastIfNoneMatch']!r}."
            )

            context.close()
        finally:
            browser.close()
