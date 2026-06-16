import json
import os
import shutil

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_node_binary_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npm_binary_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_npx_binary_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH."


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist."
    )


def test_package_json_exists():
    path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(path), f"Expected {path} to exist."


def test_package_json_starts_with_cordova_plugin_device():
    path = os.path.join(PROJECT_DIR, "package.json")
    with open(path) as f:
        data = json.load(f)
    deps = data.get("dependencies", {}) or {}
    dev_deps = data.get("devDependencies", {}) or {}
    assert "cordova-plugin-device" in deps or "cordova-plugin-device" in dev_deps, (
        "Expected initial package.json to declare 'cordova-plugin-device' as a "
        "dependency before migration."
    )


def test_package_json_does_not_yet_have_capacitor_device():
    path = os.path.join(PROJECT_DIR, "package.json")
    with open(path) as f:
        data = json.load(f)
    deps = data.get("dependencies", {}) or {}
    dev_deps = data.get("devDependencies", {}) or {}
    assert "@capacitor/device" not in deps and "@capacitor/device" not in dev_deps, (
        "Expected initial package.json NOT to depend on '@capacitor/device' before "
        "migration."
    )


def test_capacitor_config_exists():
    # The pre-existing Capacitor configuration file at the project root.
    path = os.path.join(PROJECT_DIR, "capacitor.config.json")
    assert os.path.isfile(path), f"Expected {path} to exist."


def test_index_html_exists_with_cordova_script_tag():
    path = os.path.join(PROJECT_DIR, "www", "index.html")
    assert os.path.isfile(path), f"Expected {path} to exist."
    with open(path) as f:
        content = f.read()
    assert "cordova.js" in content, (
        "Expected initial www/index.html to reference cordova.js before migration."
    )


def test_legacy_device_info_uses_window_device():
    path = os.path.join(PROJECT_DIR, "www", "js", "device-info.js")
    assert os.path.isfile(path), f"Expected {path} to exist."
    with open(path) as f:
        content = f.read()
    assert "window.device" in content, (
        "Expected initial www/js/device-info.js to use the legacy 'window.device' "
        "global before migration."
    )


def test_cordova_plugin_device_installed_in_node_modules():
    path = os.path.join(PROJECT_DIR, "node_modules", "cordova-plugin-device")
    assert os.path.isdir(path), (
        f"Expected the legacy plugin to be installed under {path} before migration."
    )


def test_capacitor_core_installed():
    path = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "core")
    assert os.path.isdir(path), (
        f"Expected @capacitor/core to be pre-installed under {path}."
    )


def test_capacitor_cli_installed():
    path = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "cli")
    assert os.path.isdir(path), (
        f"Expected @capacitor/cli to be pre-installed under {path}."
    )


def test_capacitor_device_not_yet_installed():
    path = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "device")
    assert not os.path.isdir(path), (
        f"Expected @capacitor/device to NOT be installed at {path} before migration."
    )


def test_sync_log_does_not_exist_yet():
    path = os.path.join(PROJECT_DIR, "sync.log")
    assert not os.path.exists(path), (
        f"Expected {path} to not exist before the agent runs the migration."
    )
