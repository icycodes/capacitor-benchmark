import json
import os
import shutil

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_node_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npm_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected Capacitor project directory at {PROJECT_DIR} to exist."
    )


def test_package_json_exists_and_has_capacitor_core():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg), f"Expected {pkg} to exist."
    with open(pkg, "r", encoding="utf-8") as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies") or {})
    deps.update(data.get("devDependencies") or {})
    assert "@capacitor/core" in deps, (
        "Expected @capacitor/core to be declared in package.json before the task starts."
    )
    assert "@capacitor/android" in deps, (
        "Expected @capacitor/android to be declared in package.json before the task starts."
    )


def test_capacitor_config_exists():
    candidates = [
        os.path.join(PROJECT_DIR, "capacitor.config.ts"),
        os.path.join(PROJECT_DIR, "capacitor.config.json"),
    ]
    assert any(os.path.isfile(p) for p in candidates), (
        "Expected a capacitor.config.ts or capacitor.config.json in the project root."
    )


def test_android_project_scaffolded():
    android_dir = os.path.join(PROJECT_DIR, "android")
    assert os.path.isdir(android_dir), (
        f"Expected scaffolded Android project at {android_dir}."
    )


def test_android_top_level_build_gradle_exists():
    p = os.path.join(PROJECT_DIR, "android", "build.gradle")
    assert os.path.isfile(p), (
        f"Expected top-level Android Gradle file at {p}."
    )


def test_android_app_build_gradle_exists():
    p = os.path.join(PROJECT_DIR, "android", "app", "build.gradle")
    assert os.path.isfile(p), (
        f"Expected app-level Android Gradle file at {p}."
    )


def test_src_directory_exists():
    src_dir = os.path.join(PROJECT_DIR, "src")
    assert os.path.isdir(src_dir), (
        f"Expected source directory at {src_dir} for TypeScript wiring."
    )


def test_push_notifications_not_yet_installed():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg, "r", encoding="utf-8") as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies") or {})
    deps.update(data.get("devDependencies") or {})
    assert "@capacitor/push-notifications" not in deps, (
        "@capacitor/push-notifications must not be pre-installed; the executor is responsible for adding it."
    )


def test_google_services_json_not_present():
    p = os.path.join(PROJECT_DIR, "android", "app", "google-services.json")
    assert not os.path.exists(p), (
        "google-services.json must not be pre-created; the executor must add it."
    )


def test_setup_log_not_present():
    p = os.path.join(PROJECT_DIR, "setup.log")
    assert not os.path.exists(p), (
        "setup.log must not exist at task start; the executor will create it."
    )
