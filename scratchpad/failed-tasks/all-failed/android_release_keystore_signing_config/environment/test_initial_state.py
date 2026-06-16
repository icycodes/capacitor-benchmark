import os
import shutil
import subprocess

import pytest

PROJECT_DIR = "/home/user/myproject"
ANDROID_DIR = os.path.join(PROJECT_DIR, "android")
APP_DIR = os.path.join(ANDROID_DIR, "app")
BUILD_GRADLE = os.path.join(APP_DIR, "build.gradle")
KEYSTORE_PROPERTIES = os.path.join(ANDROID_DIR, "keystore.properties")
KEYSTORE_PROPERTIES_EXAMPLE = os.path.join(ANDROID_DIR, "keystore.properties.example")
GRADLEW = os.path.join(ANDROID_DIR, "gradlew")


def test_node_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npx_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH."


def test_java_available():
    assert shutil.which("java") is not None, "java binary not found in PATH."


def test_keytool_available():
    assert shutil.which("keytool") is not None, (
        "keytool binary not found in PATH (required to manage release keystores)."
    )


def test_capacitor_cli_available():
    result = subprocess.run(
        ["npx", "--no-install", "cap", "--version"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Capacitor CLI is not available in {PROJECT_DIR}: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_android_directory_exists():
    assert os.path.isdir(ANDROID_DIR), (
        f"Android directory {ANDROID_DIR} does not exist."
    )


def test_app_directory_exists():
    assert os.path.isdir(APP_DIR), (
        f"Android app directory {APP_DIR} does not exist."
    )


def test_build_gradle_exists():
    assert os.path.isfile(BUILD_GRADLE), (
        f"Expected {BUILD_GRADLE} to exist in the bootstrapped Capacitor project."
    )


def test_build_gradle_has_no_signing_config_yet():
    with open(BUILD_GRADLE) as f:
        content = f.read()
    assert "signingConfigs" not in content, (
        "The bootstrapped android/app/build.gradle must NOT yet declare any "
        "signingConfigs block; the executor is expected to add one."
    )


def test_keystore_properties_does_not_exist_initially():
    assert not os.path.exists(KEYSTORE_PROPERTIES), (
        f"{KEYSTORE_PROPERTIES} must not be present in the initial state; "
        "real keystore secrets should never ship with the bootstrap."
    )


def test_keystore_properties_example_does_not_exist_initially():
    assert not os.path.exists(KEYSTORE_PROPERTIES_EXAMPLE), (
        f"{KEYSTORE_PROPERTIES_EXAMPLE} must not yet exist; "
        "the executor is expected to create this file."
    )


def test_gradle_wrapper_present():
    assert os.path.isfile(GRADLEW), (
        f"Gradle wrapper script {GRADLEW} is missing from the bootstrap; "
        "it is required to validate that the build.gradle still parses."
    )
    assert os.access(GRADLEW, os.X_OK), (
        f"Gradle wrapper {GRADLEW} is not executable."
    )


def test_git_repository_initialized():
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0 and result.stdout.strip() == "true", (
        f"{PROJECT_DIR} is expected to be a git repository so that "
        "`git check-ignore` can verify .gitignore rules."
    )
