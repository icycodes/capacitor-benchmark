import os
import plistlib
import shutil
import subprocess

import pytest

PROJECT_DIR = "/home/user/myapp"
INFO_PLIST = os.path.join(PROJECT_DIR, "ios", "App", "App", "Info.plist")
CAP_CONFIG = os.path.join(PROJECT_DIR, "capacitor.config.ts")


def test_node_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npx_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH."


def test_plutil_wrapper_available():
    assert shutil.which("plutil") is not None, (
        "plutil wrapper not found in PATH; the environment must provide a "
        "Linux-compatible `plutil` command."
    )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_capacitor_config_exists():
    assert os.path.isfile(CAP_CONFIG), (
        f"Capacitor config file {CAP_CONFIG} is expected to be pre-created."
    )


def test_capacitor_config_initial_fields():
    with open(CAP_CONFIG, "r", encoding="utf-8") as f:
        content = f.read()
    assert "com.example.myapp" in content, (
        "Initial capacitor.config.ts must contain appId 'com.example.myapp'."
    )
    assert "My Native App" in content, (
        "Initial capacitor.config.ts must contain appName 'My Native App'."
    )
    assert "dist" in content, (
        "Initial capacitor.config.ts must contain webDir 'dist'."
    )


def test_ios_project_scaffolded():
    assert os.path.isdir(os.path.join(PROJECT_DIR, "ios", "App", "App")), (
        "ios/App/App directory is expected to be pre-scaffolded."
    )


def test_info_plist_exists():
    assert os.path.isfile(INFO_PLIST), (
        f"Info.plist file {INFO_PLIST} is expected to be pre-created by `npx cap add ios`."
    )


def test_info_plist_initially_parses():
    with open(INFO_PLIST, "rb") as f:
        data = plistlib.load(f)
    assert isinstance(data, dict), "Info.plist must be a top-level dict."
    assert "CFBundleIdentifier" in data, (
        "Initial Info.plist should already contain CFBundleIdentifier."
    )


def test_info_plist_initially_lacks_permission_keys():
    with open(INFO_PLIST, "rb") as f:
        data = plistlib.load(f)
    for key in (
        "NSCameraUsageDescription",
        "NSMicrophoneUsageDescription",
        "NSPhotoLibraryUsageDescription",
        "NSPhotoLibraryAddUsageDescription",
    ):
        assert key not in data, (
            f"Initial Info.plist must NOT yet contain {key}; it is the executor's job to add it."
        )


def test_initial_plutil_lint_passes():
    result = subprocess.run(
        ["plutil", "-lint", INFO_PLIST],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Initial Info.plist must parse cleanly with plutil -lint. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
