import os
import re
import shutil
import subprocess

PROJECT_DIR = "/home/user/myapp"
IOS_DIR = os.path.join(PROJECT_DIR, "ios")
IOS_APP_DIR = os.path.join(IOS_DIR, "App", "App")
PBXPROJ_PATH = os.path.join(IOS_DIR, "App", "App.xcodeproj", "project.pbxproj")
MY_VC_PATH = os.path.join(IOS_APP_DIR, "MyViewController.swift")
ECHO_PLUGIN_PATH = os.path.join(IOS_APP_DIR, "EchoPlugin.swift")
SRC_DIR = os.path.join(PROJECT_DIR, "src")
ECHO_TS_PATH = os.path.join(SRC_DIR, "echo.ts")


def test_node_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npm_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_npx_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_package_json_exists():
    package_json_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(package_json_path), f"package.json not found at {package_json_path}."


def test_capacitor_config_exists():
    # The bootstrap project should have either capacitor.config.ts or capacitor.config.json.
    candidates = [
        os.path.join(PROJECT_DIR, "capacitor.config.ts"),
        os.path.join(PROJECT_DIR, "capacitor.config.json"),
        os.path.join(PROJECT_DIR, "capacitor.config.js"),
    ]
    assert any(os.path.isfile(p) for p in candidates), (
        "Expected a capacitor.config.{ts,json,js} file in the project root."
    )


def test_ios_platform_present():
    assert os.path.isdir(IOS_DIR), f"iOS platform directory {IOS_DIR} does not exist."
    assert os.path.isdir(IOS_APP_DIR), f"iOS App source directory {IOS_APP_DIR} does not exist."


def test_pbxproj_exists():
    assert os.path.isfile(PBXPROJ_PATH), f"Xcode project file {PBXPROJ_PATH} does not exist."


def test_myviewcontroller_exists():
    assert os.path.isfile(MY_VC_PATH), (
        f"Pre-scaffolded view controller {MY_VC_PATH} does not exist."
    )


def test_myviewcontroller_subclasses_bridge_view_controller():
    with open(MY_VC_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert re.search(
        r"class\s+MyViewController\s*:\s*CAPBridgeViewController",
        content,
    ), "MyViewController.swift must subclass CAPBridgeViewController in the initial state."


def test_initial_no_echo_plugin_swift():
    assert not os.path.exists(ECHO_PLUGIN_PATH), (
        f"EchoPlugin.swift must NOT exist in the initial state ({ECHO_PLUGIN_PATH})."
    )


def test_initial_pbxproj_no_echo_plugin_reference():
    with open(PBXPROJ_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "EchoPlugin.swift" not in content, (
        "project.pbxproj must NOT reference EchoPlugin.swift in the initial state."
    )


def test_initial_myviewcontroller_does_not_register_echo():
    with open(MY_VC_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "registerPluginInstance(EchoPlugin" not in content, (
        "MyViewController.swift must NOT register EchoPlugin in the initial state."
    )


def test_initial_no_echo_ts_wrapper():
    assert not os.path.exists(ECHO_TS_PATH), (
        f"src/echo.ts must NOT exist in the initial state ({ECHO_TS_PATH})."
    )


def test_capacitor_cli_available():
    # Run via npx, which is provided by the npm install in the Dockerfile.
    result = subprocess.run(
        ["npx", "--no-install", "cap", "--version"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"`npx cap --version` failed in {PROJECT_DIR}. stdout={result.stdout!r} stderr={result.stderr!r}"
    )
