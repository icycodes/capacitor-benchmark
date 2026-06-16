import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

PROJECT_DIR = "/home/user/myapp"
ANDROID_DIR = os.path.join(PROJECT_DIR, "android")
ANDROID_APP_MAIN = os.path.join(ANDROID_DIR, "app", "src", "main")
CAPACITOR_CONFIG = os.path.join(PROJECT_DIR, "capacitor.config.ts")
ANDROID_MANIFEST = os.path.join(ANDROID_APP_MAIN, "AndroidManifest.xml")
NETWORK_SECURITY_XML = os.path.join(
    ANDROID_APP_MAIN, "res", "xml", "network_security_config.xml"
)
SYNC_LOG = os.path.join(PROJECT_DIR, "sync.log")


def test_node_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npx_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_capacitor_config_exists():
    assert os.path.isfile(CAPACITOR_CONFIG), (
        f"capacitor.config.ts not found at {CAPACITOR_CONFIG}."
    )


def test_capacitor_config_initial_values_present():
    with open(CAPACITOR_CONFIG, "r", encoding="utf-8") as f:
        content = f.read()
    assert "com.example.myapp" in content, (
        "Initial appId 'com.example.myapp' should be present in capacitor.config.ts."
    )
    assert "My Native App" in content, (
        "Initial appName 'My Native App' should be present in capacitor.config.ts."
    )
    assert "dist" in content, (
        "Initial webDir 'dist' should be present in capacitor.config.ts."
    )


def test_capacitor_config_does_not_yet_set_https_scheme():
    with open(CAPACITOR_CONFIG, "r", encoding="utf-8") as f:
        content = f.read()
    assert "myapp.example.com" not in content, (
        "Custom hostname 'myapp.example.com' must NOT be present in the initial "
        "capacitor.config.ts — it is what the task expects the executor to add."
    )


def test_package_json_has_capacitor_cli():
    package_json = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(package_json), f"package.json not found at {package_json}."
    with open(package_json, "r", encoding="utf-8") as f:
        content = f.read()
    assert "@capacitor/cli" in content, (
        "@capacitor/cli must be listed in package.json so `npx cap` works."
    )
    assert "@capacitor/android" in content, (
        "@capacitor/android must be listed in package.json."
    )


def test_node_modules_capacitor_cli_installed():
    cli_dir = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "cli")
    assert os.path.isdir(cli_dir), (
        f"@capacitor/cli must be installed under {cli_dir} (run `npm install` "
        "during bootstrap)."
    )
    android_pkg = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "android")
    assert os.path.isdir(android_pkg), (
        f"@capacitor/android must be installed under {android_pkg}."
    )


def test_dist_web_assets_exist():
    dist_index = os.path.join(PROJECT_DIR, "dist", "index.html")
    assert os.path.isfile(dist_index), (
        f"Web assets directory `dist/` must contain index.html ({dist_index})."
    )


def test_android_platform_added():
    assert os.path.isdir(ANDROID_DIR), (
        f"Android platform directory {ANDROID_DIR} must already be present."
    )
    assert os.path.isfile(ANDROID_MANIFEST), (
        f"AndroidManifest.xml must already exist at {ANDROID_MANIFEST}."
    )


def test_android_manifest_initial_state_has_no_network_security_config():
    tree = ET.parse(ANDROID_MANIFEST)
    root = tree.getroot()
    ns = "{http://schemas.android.com/apk/res/android}"
    application = root.find("application")
    assert application is not None, (
        "AndroidManifest.xml must contain an <application> element."
    )
    assert application.get(f"{ns}networkSecurityConfig") is None, (
        "Initial AndroidManifest.xml should NOT yet reference a "
        "networkSecurityConfig — the executor will add it."
    )


def test_network_security_config_xml_does_not_exist_initially():
    assert not os.path.exists(NETWORK_SECURITY_XML), (
        f"{NETWORK_SECURITY_XML} must NOT exist initially — the executor will create it."
    )


def test_sync_log_does_not_exist_initially():
    assert not os.path.exists(SYNC_LOG), (
        f"{SYNC_LOG} must NOT exist initially — the executor will produce it."
    )


def test_capacitor_cli_runs():
    result = subprocess.run(
        ["npx", "--no-install", "cap", "--version"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        "`npx cap --version` must succeed in the project directory. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
