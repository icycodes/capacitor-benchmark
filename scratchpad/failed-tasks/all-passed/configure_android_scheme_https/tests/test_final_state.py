import json
import os
import shutil
import subprocess

import pytest

PROJECT_DIR = "/home/user/myapp"
CONFIG_TS = os.path.join(PROJECT_DIR, "capacitor.config.ts")
CONFIG_JSON = os.path.join(PROJECT_DIR, "capacitor.config.json")
DIST_INDEX = os.path.join(PROJECT_DIR, "dist", "index.html")
INITIAL_RECORD_PATH = "/home/user/.harbor/initial_capacitor_config.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_effective_config() -> dict:
    """Evaluate the agent's capacitor.config.ts/json and return the exported object."""
    if os.path.isfile(CONFIG_TS):
        # Use tsx to evaluate the TypeScript config and emit JSON on stdout.
        loader = (
            "import('./capacitor.config.ts').then((m) => {"
            "process.stdout.write(JSON.stringify(m.default ?? m));"
            "}).catch((err) => {"
            "console.error(err && err.stack || err); process.exit(1);"
            "});"
        )
        result = subprocess.run(
            ["npx", "--no-install", "tsx", "-e", loader],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert result.returncode == 0, (
            f"Failed to evaluate capacitor.config.ts via tsx (exit {result.returncode}).\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        try:
            return json.loads(result.stdout.strip())
        except json.JSONDecodeError as exc:
            pytest.fail(
                f"capacitor.config.ts did not produce valid JSON output: {exc}\n"
                f"stdout was: {result.stdout!r}"
            )
    elif os.path.isfile(CONFIG_JSON):
        with open(CONFIG_JSON, encoding="utf-8") as fh:
            return json.load(fh)
    else:
        pytest.fail(
            f"Neither {CONFIG_TS} nor {CONFIG_JSON} exists; Capacitor config is missing."
        )


def _load_initial_record() -> dict:
    assert os.path.isfile(INITIAL_RECORD_PATH), (
        f"Initial Capacitor config record not found at {INITIAL_RECORD_PATH}."
    )
    with open(INITIAL_RECORD_PATH, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_capacitor_config_exists():
    assert os.path.isfile(CONFIG_TS) or os.path.isfile(CONFIG_JSON), (
        f"Expected a Capacitor config at {CONFIG_TS} or {CONFIG_JSON}."
    )


def test_server_android_scheme_is_https():
    config = _load_effective_config()
    server = config.get("server")
    assert isinstance(server, dict), (
        f"Capacitor config must define a 'server' object. Got: {server!r}"
    )
    assert server.get("androidScheme") == "https", (
        f"Expected server.androidScheme == 'https', got {server.get('androidScheme')!r}."
    )


def test_server_hostname_is_custom():
    config = _load_effective_config()
    server = config.get("server")
    assert isinstance(server, dict), (
        f"Capacitor config must define a 'server' object. Got: {server!r}"
    )
    assert server.get("hostname") == "myapp.example.com", (
        f"Expected server.hostname == 'myapp.example.com', got {server.get('hostname')!r}."
    )


def test_app_metadata_preserved():
    config = _load_effective_config()
    initial = _load_initial_record()
    for key in ("appId", "appName", "webDir"):
        assert config.get(key) == initial[key], (
            f"Capacitor config field {key!r} changed: "
            f"initial={initial[key]!r}, current={config.get(key)!r}. "
            "Pre-existing app metadata must not be modified."
        )


def test_npm_build_succeeds_and_produces_index_html():
    # Force a clean rebuild so we exercise the script, not stale artifacts.
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
        f"`npm run build` failed with exit code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert os.path.isfile(DIST_INDEX), (
        f"Expected built output {DIST_INDEX} to exist after `npm run build`."
    )


def test_cap_sync_succeeds():
    result = subprocess.run(
        ["npx", "--no-install", "cap", "sync"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, (
        f"`npx cap sync` failed with exit code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
