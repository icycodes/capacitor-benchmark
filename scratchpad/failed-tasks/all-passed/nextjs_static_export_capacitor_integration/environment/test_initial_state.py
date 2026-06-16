import json
import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myapp"


def test_node_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_node_version_22_or_higher():
    result = subprocess.run(
        ["node", "--version"], capture_output=True, text=True, check=True
    )
    version = result.stdout.strip().lstrip("v")
    major = int(version.split(".")[0])
    assert major >= 22, f"Expected Node.js >= 22, got {version}."


def test_npm_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_npx_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH."


def test_java_available():
    assert shutil.which("java") is not None, "java binary not found in PATH."


def test_android_sdk_root_set():
    sdk_root = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    assert sdk_root, "ANDROID_SDK_ROOT/ANDROID_HOME environment variable is not set."
    assert os.path.isdir(sdk_root), f"Android SDK directory {sdk_root} does not exist."


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_package_json_present_with_nextjs_14():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), f"{pkg_path} does not exist."
    with open(pkg_path) as f:
        pkg = json.load(f)
    deps = pkg.get("dependencies", {})
    assert "next" in deps, "next is not declared in package.json dependencies."
    assert deps["next"].startswith("14") or "14." in deps["next"], (
        f"Expected Next.js 14 (got {deps['next']!r})."
    )
    assert "react" in deps, "react is not declared in package.json dependencies."
    assert "react-dom" in deps, (
        "react-dom is not declared in package.json dependencies."
    )


def test_capacitor_packages_not_yet_declared():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg_path) as f:
        pkg = json.load(f)
    deps = pkg.get("dependencies", {})
    dev_deps = pkg.get("devDependencies", {})
    for name in ("@capacitor/core", "@capacitor/android", "@capacitor/cli"):
        assert name not in deps and name not in dev_deps, (
            f"{name} should not be declared in package.json before the task starts."
        )


def test_node_modules_next_installed():
    next_pkg = os.path.join(PROJECT_DIR, "node_modules", "next", "package.json")
    assert os.path.isfile(next_pkg), (
        f"next is not installed under node_modules at {next_pkg}."
    )


def test_default_next_config_present_without_static_export():
    candidates = [
        os.path.join(PROJECT_DIR, "next.config.js"),
        os.path.join(PROJECT_DIR, "next.config.mjs"),
    ]
    found = [p for p in candidates if os.path.isfile(p)]
    assert found, (
        f"Expected a default next.config.js (or next.config.mjs) in {PROJECT_DIR}."
    )
    content = open(found[0]).read()
    assert "output:" not in content or "'export'" not in content, (
        "next.config should NOT yet declare output: 'export' before the task starts."
    )


def test_app_router_pages_present():
    app_dir = os.path.join(PROJECT_DIR, "app")
    assert os.path.isdir(app_dir), f"App Router directory {app_dir} does not exist."
    assert os.path.isfile(os.path.join(app_dir, "layout.tsx")), (
        "Expected app/layout.tsx to be present before the task starts."
    )
    assert os.path.isfile(os.path.join(app_dir, "page.tsx")), (
        "Expected app/page.tsx to be present before the task starts."
    )


def test_capacitor_config_not_yet_present():
    for fname in ("capacitor.config.ts", "capacitor.config.json"):
        path = os.path.join(PROJECT_DIR, fname)
        assert not os.path.exists(path), (
            f"{path} should not exist before the task starts."
        )


def test_android_platform_not_yet_present():
    android_dir = os.path.join(PROJECT_DIR, "android")
    assert not os.path.exists(android_dir), (
        f"{android_dir} should not exist before the task starts."
    )


def test_hash_router_helper_not_yet_present():
    helper = os.path.join(PROJECT_DIR, "lib", "hashRouter.ts")
    assert not os.path.exists(helper), (
        f"{helper} should not exist before the task starts."
    )


def test_out_directory_not_yet_present():
    out_dir = os.path.join(PROJECT_DIR, "out")
    assert not os.path.exists(out_dir), (
        f"{out_dir} should not exist before the task starts."
    )
