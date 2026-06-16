import json
import os
import re
import subprocess

import pytest

PROJECT_DIR = "/home/user/myproject"
SYNC_LOG = os.path.join(PROJECT_DIR, "sync.log")
WWW_DIR = os.path.join(PROJECT_DIR, "www")
INDEX_HTML = os.path.join(WWW_DIR, "index.html")
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")


def _find_reader_path():
    """Return the path of the migrated reader script, preferring .mjs over .js."""
    candidates = [
        os.path.join(SCRIPTS_DIR, "device-report.mjs"),
        os.path.join(SCRIPTS_DIR, "device-report.js"),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def _iter_files(root):
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            yield os.path.join(dirpath, name)


# --- 1. Sync log produced by the agent --------------------------------------


def test_sync_log_exists_and_indicates_success():
    assert os.path.isfile(SYNC_LOG), (
        f"Expected sync log at {SYNC_LOG} produced by the agent's `npx cap sync` run."
    )
    with open(SYNC_LOG, "r", errors="replace") as f:
        content = f.read()
    assert content.strip(), f"Sync log {SYNC_LOG} is empty."
    assert "sync finished" in content, (
        "Expected the sync log to contain the literal substring 'sync finished' "
        "indicating a successful `npx cap sync` run."
    )


# --- 2. Cordova plugin removed ----------------------------------------------


def test_package_json_does_not_depend_on_cordova_plugin_device():
    with open(os.path.join(PROJECT_DIR, "package.json")) as f:
        data = json.load(f)
    deps = data.get("dependencies", {}) or {}
    dev_deps = data.get("devDependencies", {}) or {}
    assert "cordova-plugin-device" not in deps, (
        "Expected `cordova-plugin-device` to be removed from dependencies."
    )
    assert "cordova-plugin-device" not in dev_deps, (
        "Expected `cordova-plugin-device` to be removed from devDependencies."
    )


def test_cordova_plugin_device_removed_from_node_modules():
    legacy_path = os.path.join(PROJECT_DIR, "node_modules", "cordova-plugin-device")
    assert not os.path.isdir(legacy_path), (
        f"Expected `cordova-plugin-device` to be uninstalled (still present at {legacy_path})."
    )


# --- 3. Capacitor Device plugin installed -----------------------------------


def test_package_json_depends_on_capacitor_device():
    with open(os.path.join(PROJECT_DIR, "package.json")) as f:
        data = json.load(f)
    deps = data.get("dependencies", {}) or {}
    assert "@capacitor/device" in deps, (
        "Expected `@capacitor/device` to appear in `dependencies` of package.json."
    )


def test_capacitor_device_present_in_node_modules():
    path = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "device")
    assert os.path.isdir(path), (
        f"Expected `@capacitor/device` to be installed at {path}."
    )


# --- 4. `cordova.js` removed from index.html --------------------------------


def test_index_html_does_not_reference_cordova_js():
    assert os.path.isfile(INDEX_HTML), f"Expected {INDEX_HTML} to exist."
    with open(INDEX_HTML) as f:
        content = f.read()
    assert "cordova.js" not in content, (
        f"Expected all references to `cordova.js` to be removed from {INDEX_HTML}."
    )


# --- 5. No `window.device` / `cordova.plugins.device` usages ----------------


def test_no_legacy_window_device_usages_under_www():
    offenders = []
    for path in _iter_files(WWW_DIR):
        try:
            with open(path, "r", errors="replace") as f:
                content = f.read()
        except OSError:
            continue
        if "window.device" in content or "cordova.plugins.device" in content:
            offenders.append(path)
    assert not offenders, (
        "Expected no remaining `window.device` or `cordova.plugins.device` usages "
        f"under {WWW_DIR}, but found them in: {offenders}"
    )


# --- 6. Reader source uses the new API --------------------------------------


def test_migrated_reader_script_exists():
    path = _find_reader_path()
    assert path is not None, (
        "Expected a migrated reader script at "
        f"{os.path.join(SCRIPTS_DIR, 'device-report.mjs')} or "
        f"{os.path.join(SCRIPTS_DIR, 'device-report.js')}."
    )


def test_migrated_reader_imports_capacitor_device():
    path = _find_reader_path()
    assert path is not None, "Migrated reader script not found."
    with open(path) as f:
        source = f.read()
    pattern = re.compile(
        r"""(from\s+['"]@capacitor/device['"])|(require\(\s*['"]@capacitor/device['"]\s*\))"""
    )
    assert pattern.search(source), (
        f"Expected {path} to import from `@capacitor/device` "
        "(either via ES module `from '@capacitor/device'` or CommonJS "
        "`require('@capacitor/device')`)."
    )


def test_migrated_reader_uses_all_three_device_apis():
    path = _find_reader_path()
    assert path is not None, "Migrated reader script not found."
    with open(path) as f:
        source = f.read()
    for needle in ("Device.getInfo", "Device.getId", "Device.getBatteryInfo"):
        assert needle in source, (
            f"Expected migrated reader at {path} to call `{needle}`."
        )
    assert "await" in source, (
        f"Expected migrated reader at {path} to use `await` for the asynchronous "
        "Capacitor Device API calls."
    )


# --- 7. Reader runs and prints valid JSON -----------------------------------


def test_migrated_reader_runs_and_prints_valid_json():
    path = _find_reader_path()
    assert path is not None, "Migrated reader script not found."
    result = subprocess.run(
        ["node", path],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"Expected `node {path}` to exit 0. stderr:\n{result.stderr}\nstdout:\n{result.stdout}"
    )
    stdout = result.stdout.strip()
    assert stdout, (
        f"Expected `node {path}` to write JSON to stdout, but stdout was empty. "
        f"stderr:\n{result.stderr}"
    )
    # Tolerate the JSON being either the entire stdout or the last printed line.
    payload = None
    for candidate in (stdout, stdout.splitlines()[-1]):
        try:
            payload = json.loads(candidate)
            break
        except json.JSONDecodeError:
            continue
    assert payload is not None, (
        f"Expected stdout of `node {path}` to be JSON-parseable. Got: {stdout!r}"
    )
    # Validate the expected shape.
    info = payload.get("info")
    assert isinstance(info, dict), f"Expected 'info' object in output, got: {payload}"
    assert info.get("platform") == "web", (
        f"Expected info.platform == 'web' under Node, got: {info.get('platform')!r}"
    )
    for key in ("operatingSystem", "osVersion", "manufacturer", "model", "webViewVersion"):
        assert isinstance(info.get(key), str), (
            f"Expected info.{key} to be a string, got: {info.get(key)!r}"
        )
    assert isinstance(info.get("isVirtual"), bool), (
        f"Expected info.isVirtual to be a boolean, got: {info.get('isVirtual')!r}"
    )

    identifier_obj = payload.get("id")
    assert isinstance(identifier_obj, dict), (
        f"Expected 'id' object in output, got: {payload}"
    )
    identifier = identifier_obj.get("identifier")
    assert isinstance(identifier, str) and identifier, (
        f"Expected id.identifier to be a non-empty string, got: {identifier!r}"
    )

    battery = payload.get("battery")
    assert isinstance(battery, dict), (
        f"Expected 'battery' object in output, got: {payload}"
    )
    level = battery.get("batteryLevel")
    assert isinstance(level, (int, float)) and 0 <= float(level) <= 1, (
        f"Expected battery.batteryLevel to be a number in [0, 1], got: {level!r}"
    )
    assert isinstance(battery.get("isCharging"), bool), (
        f"Expected battery.isCharging to be a boolean, got: {battery.get('isCharging')!r}"
    )


# --- 8. `npx cap sync` succeeds when re-run by the verifier -----------------


def test_npx_cap_sync_runs_clean():
    result = subprocess.run(
        ["npx", "cap", "sync"],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Expected `npx cap sync` to exit 0 after migration. "
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    combined = result.stdout + result.stderr
    assert "sync finished" in combined, (
        "Expected `npx cap sync` output to include 'sync finished'. "
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
