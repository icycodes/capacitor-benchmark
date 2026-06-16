import json
import os
import re
import shutil

PROJECT_DIR = "/home/user/myapp"


def test_node_available():
    assert shutil.which("node") is not None, "Node.js is not available in PATH."


def test_npm_available():
    assert shutil.which("npm") is not None, "npm is not available in PATH."


def test_npx_available():
    assert shutil.which("npx") is not None, "npx is not available in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_package_json_exists_and_is_v7():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), f"{pkg_path} is missing in the initial state."
    with open(pkg_path) as f:
        pkg = json.load(f)
    deps = {}
    deps.update(pkg.get("dependencies", {}) or {})
    deps.update(pkg.get("devDependencies", {}) or {})
    for name in ("@capacitor/core", "@capacitor/cli", "@capacitor/android"):
        assert name in deps, f"Expected {name} to be present in package.json before upgrade."
        version = deps[name]
        assert "7" in version and "8" not in version, (
            f"Expected {name} to be pinned to a Capacitor 7 version initially, got {version!r}."
        )


def test_capacitor_config_exists():
    candidates = [
        os.path.join(PROJECT_DIR, "capacitor.config.json"),
        os.path.join(PROJECT_DIR, "capacitor.config.ts"),
    ]
    assert any(os.path.isfile(p) for p in candidates), (
        "Expected a capacitor.config.json or capacitor.config.ts at the project root."
    )


def test_android_project_present():
    android_dir = os.path.join(PROJECT_DIR, "android")
    assert os.path.isdir(android_dir), f"{android_dir} should exist (committed native platform)."

    build_gradle = os.path.join(android_dir, "build.gradle")
    assert os.path.isfile(build_gradle), f"{build_gradle} is missing."

    wrapper_props = os.path.join(android_dir, "gradle", "wrapper", "gradle-wrapper.properties")
    assert os.path.isfile(wrapper_props), f"{wrapper_props} is missing."

    variables_gradle = os.path.join(android_dir, "variables.gradle")
    assert os.path.isfile(variables_gradle), f"{variables_gradle} is missing."

    main_activity = os.path.join(
        android_dir,
        "app",
        "src",
        "main",
        "java",
        "com",
        "example",
        "myapp",
        "MainActivity.java",
    )
    assert os.path.isfile(main_activity), f"{main_activity} is missing."


def test_android_starts_on_v7_toolchain():
    """Ensure the project really starts on the old toolchain so the upgrade is non-trivial."""
    with open(os.path.join(PROJECT_DIR, "android", "build.gradle")) as f:
        build_gradle = f.read()
    assert re.search(r"com\.android\.tools\.build:gradle:8\.2\.\d+", build_gradle), (
        "Expected initial android/build.gradle to use Android Gradle Plugin 8.2.x."
    )

    with open(os.path.join(PROJECT_DIR, "android", "gradle", "wrapper", "gradle-wrapper.properties")) as f:
        wrapper = f.read()
    assert re.search(r"gradle-8\.2\.\d+(-all|-bin)\.zip", wrapper), (
        "Expected initial gradle-wrapper.properties to use Gradle 8.2.x."
    )

    with open(os.path.join(PROJECT_DIR, "android", "variables.gradle")) as f:
        variables = f.read()
    assert re.search(r"compileSdkVersion\s*=\s*34\b", variables), (
        "Expected initial variables.gradle to set compileSdkVersion = 34."
    )
    assert re.search(r"targetSdkVersion\s*=\s*34\b", variables), (
        "Expected initial variables.gradle to set targetSdkVersion = 34."
    )
    assert re.search(r"kotlin_version\s*=\s*['\"]1\.9\.\d+['\"]", variables), (
        "Expected initial variables.gradle to set kotlin_version to 1.9.x."
    )


def test_upgrade_log_not_yet_created():
    log_path = os.path.join(PROJECT_DIR, "upgrade.log")
    assert not os.path.exists(log_path), (
        f"{log_path} should not exist before the executor runs the upgrade."
    )
