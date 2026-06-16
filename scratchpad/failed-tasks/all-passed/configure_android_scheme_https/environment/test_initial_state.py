import json
import os
import shutil
import subprocess

import pytest

PROJECT_DIR = "/home/user/myapp"
CONFIG_TS = os.path.join(PROJECT_DIR, "capacitor.config.ts")
INITIAL_RECORD_DIR = "/home/user/.harbor"
INITIAL_RECORD_PATH = os.path.join(INITIAL_RECORD_DIR, "initial_capacitor_config.json")


def test_node_binary_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npm_binary_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_npx_binary_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH."


def test_java_available():
    # `npx cap sync` for the android platform requires a JDK on PATH.
    assert shutil.which("java") is not None, "java binary not found in PATH."


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_package_json_exists():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg), f"package.json not found at {pkg}."


def test_node_modules_installed():
    nm = os.path.join(PROJECT_DIR, "node_modules")
    assert os.path.isdir(nm), f"node_modules not installed at {nm}."


def test_capacitor_core_installed():
    pkg = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "core", "package.json")
    assert os.path.isfile(pkg), "@capacitor/core is not installed in node_modules."


def test_capacitor_cli_installed():
    pkg = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "cli", "package.json")
    assert os.path.isfile(pkg), "@capacitor/cli is not installed in node_modules."


def test_capacitor_android_installed():
    pkg = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "android", "package.json")
    assert os.path.isfile(pkg), "@capacitor/android is not installed in node_modules."


def test_capacitor_config_ts_exists():
    assert os.path.isfile(CONFIG_TS), f"capacitor.config.ts not found at {CONFIG_TS}."


def test_capacitor_config_initial_app_scheme():
    # The bootstrap config uses the buggy custom Android scheme described in the
    # research plan (Friction Point 3). The agent is expected to update it.
    with open(CONFIG_TS, encoding="utf-8") as fh:
        content = fh.read()
    assert "androidScheme: 'app'" in content or 'androidScheme: "app"' in content, (
        "Expected initial capacitor.config.ts to declare server.androidScheme as 'app'."
    )
    assert "myapp.example.com" not in content, (
        "Initial capacitor.config.ts must NOT already contain the target hostname."
    )


def test_android_platform_scaffolded():
    android_dir = os.path.join(PROJECT_DIR, "android")
    assert os.path.isdir(android_dir), (
        f"Android native project directory {android_dir} must be pre-scaffolded."
    )
    gradle = os.path.join(android_dir, "build.gradle")
    assert os.path.isfile(gradle), f"Expected {gradle} to exist after `cap add android`."


def test_initial_config_record_captured():
    # The Dockerfile records the initial config (appId/appName/webDir) so that the
    # final-state verifier can confirm those fields are preserved.
    assert os.path.isfile(INITIAL_RECORD_PATH), (
        f"Initial config record {INITIAL_RECORD_PATH} must exist before evaluation."
    )
    with open(INITIAL_RECORD_PATH, encoding="utf-8") as fh:
        record = json.load(fh)
    for key in ("appId", "appName", "webDir"):
        assert key in record and isinstance(record[key], str) and record[key], (
            f"Initial config record is missing required field {key!r}."
        )


def test_capacitor_cli_usable():
    # Confirm the Capacitor CLI runs (this also implicitly checks Node version).
    result = subprocess.run(
        ["npx", "--no-install", "cap", "--version"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"`npx cap --version` failed with code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
