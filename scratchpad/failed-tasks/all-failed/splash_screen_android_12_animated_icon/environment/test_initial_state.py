import json
import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myproject"
ANDROID_DIR = os.path.join(PROJECT_DIR, "android")
STYLES_PATH = os.path.join(
    ANDROID_DIR, "app", "src", "main", "res", "values", "styles.xml"
)
DRAWABLE_DIR = os.path.join(ANDROID_DIR, "app", "src", "main", "res", "drawable")
CAPACITOR_CONFIG_JSON = os.path.join(PROJECT_DIR, "capacitor.config.json")
SRC_DIR = os.path.join(PROJECT_DIR, "src")
PKG_JSON = os.path.join(PROJECT_DIR, "package.json")


def test_node_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npm_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_npx_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_package_json_exists():
    assert os.path.isfile(PKG_JSON), f"package.json not found at {PKG_JSON}."


def test_capacitor_core_v8_installed():
    pkg_path = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "core", "package.json"
    )
    assert os.path.isfile(pkg_path), (
        f"@capacitor/core is not installed at {pkg_path}; the project is expected to "
        "ship with Capacitor v8 already installed."
    )
    with open(pkg_path) as f:
        data = json.load(f)
    version = data.get("version", "")
    assert version.startswith("8."), (
        f"@capacitor/core should be a v8 release; found version {version!r}."
    )


def test_capacitor_cli_available():
    pkg_path = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "cli", "package.json"
    )
    assert os.path.isfile(pkg_path), (
        f"@capacitor/cli is not installed at {pkg_path}; the project is expected to "
        "ship with the Capacitor v8 CLI already installed."
    )


def test_splash_screen_plugin_not_installed_initially():
    pkg_path = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "splash-screen", "package.json"
    )
    assert not os.path.exists(pkg_path), (
        "@capacitor/splash-screen should NOT be installed in the initial state. "
        "The executor is expected to install it as part of the task."
    )
    with open(PKG_JSON) as f:
        data = json.load(f)
    deps = data.get("dependencies", {}) or {}
    dev = data.get("devDependencies", {}) or {}
    assert "@capacitor/splash-screen" not in deps, (
        "@capacitor/splash-screen should not be present in package.json dependencies "
        "in the initial state."
    )
    assert "@capacitor/splash-screen" not in dev, (
        "@capacitor/splash-screen should not be present in package.json devDependencies "
        "in the initial state."
    )


def test_capacitor_config_json_exists():
    assert os.path.isfile(CAPACITOR_CONFIG_JSON), (
        f"capacitor.config.json not found at {CAPACITOR_CONFIG_JSON}."
    )
    with open(CAPACITOR_CONFIG_JSON) as f:
        data = json.load(f)
    plugins = data.get("plugins") or {}
    assert "SplashScreen" not in plugins, (
        "capacitor.config.json should not contain a plugins.SplashScreen entry yet; "
        "the executor is expected to add it."
    )


def test_android_platform_exists():
    assert os.path.isdir(ANDROID_DIR), (
        f"Android platform directory {ANDROID_DIR} does not exist; the task expects "
        "a scaffolded Capacitor Android project."
    )


def test_styles_xml_exists_without_splash_attrs():
    assert os.path.isfile(STYLES_PATH), (
        f"styles.xml not found at {STYLES_PATH}; the task expects the standard "
        "Capacitor Android resources to be present."
    )
    with open(STYLES_PATH) as f:
        content = f.read()
    assert "AppTheme.NoActionBarLaunch" in content, (
        "AppTheme.NoActionBarLaunch style is expected to already exist in styles.xml."
    )
    assert "windowSplashScreenAnimatedIcon" not in content, (
        "windowSplashScreenAnimatedIcon should not yet be present in styles.xml in "
        "the initial state."
    )
    assert "windowSplashScreenAnimationDuration" not in content, (
        "windowSplashScreenAnimationDuration should not yet be present in styles.xml "
        "in the initial state."
    )


def test_drawable_directory_exists_without_splash_icon():
    assert os.path.isdir(DRAWABLE_DIR), (
        f"Drawable directory {DRAWABLE_DIR} must exist in the initial state."
    )
    splash_icon = os.path.join(DRAWABLE_DIR, "splash_icon.xml")
    assert not os.path.exists(splash_icon), (
        f"{splash_icon} should not exist in the initial state; the executor is "
        "expected to create it."
    )


def test_src_directory_exists():
    assert os.path.isdir(SRC_DIR), (
        f"Web source directory {SRC_DIR} must exist so the executor can wire the "
        "JavaScript SplashScreen.hide() call into the app."
    )


def test_node_modules_present():
    node_modules = os.path.join(PROJECT_DIR, "node_modules")
    assert os.path.isdir(node_modules), (
        f"node_modules must already be installed at {node_modules}."
    )


def test_offline_npm_registry_reachable():
    # The Docker image ships with a local Verdaccio cache. We do not require it,
    # but we surface a clear failure if npm is mis-configured.
    result = subprocess.run(
        ["npm", "config", "get", "registry"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"`npm config get registry` failed: {result.stderr.strip()}"
    )
    registry = result.stdout.strip()
    assert registry.startswith("http"), (
        f"npm registry should be a URL; got {registry!r}."
    )
