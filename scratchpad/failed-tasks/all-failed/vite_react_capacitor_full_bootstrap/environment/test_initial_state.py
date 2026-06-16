import os
import shutil
import subprocess

WORKSPACE_DIR = "/home/user/workspace"
MYAPP_DIR = "/home/user/workspace/myapp"


def test_node_binary_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npm_binary_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_npx_binary_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH."


def test_node_major_version_at_least_22():
    result = subprocess.run(
        ["node", "--version"], capture_output=True, text=True, check=True
    )
    version = result.stdout.strip().lstrip("v")
    major = int(version.split(".")[0])
    assert major >= 22, (
        f"Capacitor v8 requires Node.js 22+, found v{version}."
    )


def test_java_binary_available():
    assert shutil.which("java") is not None, (
        "java binary not found in PATH (required to build the Android project)."
    )


def test_android_sdk_root_env_set():
    sdk_root = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    assert sdk_root is not None and os.path.isdir(sdk_root), (
        "ANDROID_SDK_ROOT/ANDROID_HOME must point to an installed Android SDK directory."
    )


def test_workspace_directory_exists():
    assert os.path.isdir(WORKSPACE_DIR), (
        f"Expected empty workspace directory {WORKSPACE_DIR} to exist before evaluation."
    )


def test_workspace_does_not_contain_myapp_yet():
    assert not os.path.exists(MYAPP_DIR), (
        f"Expected {MYAPP_DIR} to NOT exist before the task is performed; "
        "the executor must scaffold it from scratch."
    )
