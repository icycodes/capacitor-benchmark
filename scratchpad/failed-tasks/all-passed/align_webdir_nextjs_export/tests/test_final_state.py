import os
import re
import shutil
import subprocess

import pytest

PROJECT_DIR = "/home/user/myapp"

NEXT_CONFIG_CANDIDATES = [
    os.path.join(PROJECT_DIR, "next.config.js"),
    os.path.join(PROJECT_DIR, "next.config.mjs"),
    os.path.join(PROJECT_DIR, "next.config.ts"),
]

CAPACITOR_CONFIG_CANDIDATES = [
    os.path.join(PROJECT_DIR, "capacitor.config.ts"),
    os.path.join(PROJECT_DIR, "capacitor.config.json"),
]

OUTPUT_EXPORT_PATTERN = re.compile(r"output\s*:\s*['\"]export['\"]")
WEBDIR_OUT_PATTERN = re.compile(r"webDir\s*:\s*['\"]out['\"]")


def _read_first_existing(paths):
    for path in paths:
        if os.path.isfile(path):
            with open(path) as f:
                return path, f.read()
    return None, None


def test_next_config_enables_static_export():
    path, content = _read_first_existing(NEXT_CONFIG_CANDIDATES)
    assert path is not None, (
        "Expected one of next.config.js / next.config.mjs / next.config.ts to exist, "
        f"checked: {NEXT_CONFIG_CANDIDATES}"
    )
    assert OUTPUT_EXPORT_PATTERN.search(content or ""), (
        f"{path} must enable Next.js static export by setting output to 'export'. "
        "Expected a declaration matching the pattern output: 'export'."
    )


def test_capacitor_config_webdir_out():
    path, content = _read_first_existing(CAPACITOR_CONFIG_CANDIDATES)
    assert path is not None, (
        "Expected one of capacitor.config.ts / capacitor.config.json to exist, "
        f"checked: {CAPACITOR_CONFIG_CANDIDATES}"
    )
    assert WEBDIR_OUT_PATTERN.search(content or ""), (
        f"{path} must keep webDir set to \"out\" so Capacitor reads from the Next.js export."
    )


@pytest.fixture(scope="module")
def clean_build_outputs():
    for name in ("out", ".next"):
        target = os.path.join(PROJECT_DIR, name)
        if os.path.isdir(target):
            shutil.rmtree(target)
    yield


@pytest.fixture(scope="module")
def npm_build_result(clean_build_outputs):
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return result


def test_npm_build_exits_zero(npm_build_result):
    assert npm_build_result.returncode == 0, (
        "`npm run build` must exit with code 0 in "
        f"{PROJECT_DIR}. stdout={npm_build_result.stdout}\nstderr={npm_build_result.stderr}"
    )


def test_npm_build_produces_index_html(npm_build_result):
    assert npm_build_result.returncode == 0, (
        "`npm run build` failed; cannot validate static export output."
    )
    index_html = os.path.join(PROJECT_DIR, "out", "index.html")
    assert os.path.isfile(index_html), (
        f"Expected static export to produce {index_html} after `npm run build`."
    )


@pytest.fixture(scope="module")
def cap_sync_result(npm_build_result):
    if npm_build_result.returncode != 0:
        pytest.skip("`npm run build` failed; skipping cap sync verification.")
    result = subprocess.run(
        ["npx", "cap", "sync"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return result


def test_cap_sync_exits_zero(cap_sync_result):
    assert cap_sync_result.returncode == 0, (
        "`npx cap sync` must exit with code 0. "
        f"stdout={cap_sync_result.stdout}\nstderr={cap_sync_result.stderr}"
    )


def test_cap_sync_finds_web_assets(cap_sync_result):
    combined = (cap_sync_result.stdout or "") + "\n" + (cap_sync_result.stderr or "")
    assert "Could not find the web assets directory" not in combined, (
        "`npx cap sync` reported a missing web assets directory, indicating the "
        f"webDir does not match the build output. Output:\n{combined}"
    )
