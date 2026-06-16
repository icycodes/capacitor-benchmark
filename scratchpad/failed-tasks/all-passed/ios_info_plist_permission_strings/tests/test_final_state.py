import json
import os
import plistlib
import re
import subprocess
import tempfile

import pytest

PROJECT_DIR = "/home/user/myapp"
INFO_PLIST = os.path.join(PROJECT_DIR, "ios", "App", "App", "Info.plist")
CAP_CONFIG = os.path.join(PROJECT_DIR, "capacitor.config.ts")

PERMISSION_KEYS = [
    "NSCameraUsageDescription",
    "NSMicrophoneUsageDescription",
    "NSPhotoLibraryUsageDescription",
    "NSPhotoLibraryAddUsageDescription",
]

KEYWORD_TOKENS = {
    "NSCameraUsageDescription": ("camera", "photo", "picture", "capture"),
    "NSMicrophoneUsageDescription": (
        "microphone",
        "audio",
        "record",
        "sound",
        "voice",
    ),
    "NSPhotoLibraryUsageDescription": ("photo", "library", "gallery", "album"),
    "NSPhotoLibraryAddUsageDescription": (
        "save",
        "add",
        "store",
        "photo",
        "library",
        "gallery",
    ),
}

PRESERVED_KEYS = {
    "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
    "CFBundleName": "$(PRODUCT_NAME)",
    "CFBundleDisplayName": "MyApp",
    "UILaunchStoryboardName": "LaunchScreen",
}


@pytest.fixture(scope="module")
def info_plist_data():
    with open(INFO_PLIST, "rb") as f:
        return plistlib.load(f)


def test_plutil_lint_passes():
    result = subprocess.run(
        ["plutil", "-lint", INFO_PLIST],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`plutil -lint {INFO_PLIST}` failed with exit code {result.returncode}. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


@pytest.mark.parametrize("key", PERMISSION_KEYS)
def test_permission_key_present(info_plist_data, key):
    assert key in info_plist_data, (
        f"Required permission key {key} is missing from Info.plist."
    )


@pytest.mark.parametrize("key", PERMISSION_KEYS)
def test_permission_value_is_meaningful_string(info_plist_data, key):
    value = info_plist_data.get(key)
    assert isinstance(value, str), (
        f"{key} must be a string in Info.plist, got {type(value).__name__}."
    )
    assert len(value.strip()) >= 15, (
        f"{key} value must be at least 15 characters describing the usage, "
        f"got {value!r}."
    )
    assert value.strip() != key, (
        f"{key} value must not equal the key name itself."
    )
    lowered = value.lower()
    expected_tokens = KEYWORD_TOKENS[key]
    assert any(token in lowered for token in expected_tokens), (
        f"{key} value should reference at least one of {expected_tokens!r} in "
        f"plain English, got {value!r}."
    )


@pytest.mark.parametrize("key,expected", list(PRESERVED_KEYS.items()))
def test_preserved_plist_string_keys(info_plist_data, key, expected):
    assert key in info_plist_data, (
        f"Pre-existing key {key} was removed from Info.plist."
    )
    assert info_plist_data[key] == expected, (
        f"Pre-existing key {key} should retain value {expected!r}, "
        f"got {info_plist_data[key]!r}."
    )


def test_preserved_required_device_capabilities(info_plist_data):
    value = info_plist_data.get("UIRequiredDeviceCapabilities")
    assert value == ["armv7"], (
        f"UIRequiredDeviceCapabilities should remain ['armv7'], got {value!r}."
    )


def test_preserved_supported_interface_orientations(info_plist_data):
    value = info_plist_data.get("UISupportedInterfaceOrientations")
    assert value == [
        "UIInterfaceOrientationPortrait",
        "UIInterfaceOrientationLandscapeLeft",
        "UIInterfaceOrientationLandscapeRight",
    ], (
        "UISupportedInterfaceOrientations should retain its original portrait+"
        f"landscape values, got {value!r}."
    )


def _evaluate_capacitor_config() -> dict:
    """Evaluate capacitor.config.ts by stripping TS and running it as JS.

    Returns the resolved CapacitorConfig object as a Python dict, or raises
    RuntimeError if evaluation is not possible.
    """
    with open(CAP_CONFIG, "r", encoding="utf-8") as f:
        source = f.read()

    helper_dir = tempfile.mkdtemp(prefix="capcfg-eval-")
    js_path = os.path.join(helper_dir, "eval.mjs")
    # Strip the TypeScript-only `import { CapacitorConfig } from '@capacitor/cli';`
    # line and the `: CapacitorConfig` annotation. Keep the literal object.
    js_source = re.sub(
        r"^\s*import\s+type?\s*\{[^}]*\}\s*from\s*['\"]@capacitor/cli['\"];?\s*$",
        "",
        source,
        flags=re.MULTILINE,
    )
    js_source = re.sub(
        r"^\s*import\s+\{[^}]*\}\s*from\s*['\"]@capacitor/cli['\"];?\s*$",
        "",
        js_source,
        flags=re.MULTILINE,
    )
    js_source = re.sub(r":\s*CapacitorConfig", "", js_source)
    js_source = js_source.replace("export default config;", "")
    js_source += "\nprocess.stdout.write(JSON.stringify(config));\n"

    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js_source)

    result = subprocess.run(
        ["node", js_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to evaluate capacitor.config.ts: {result.stderr!r}"
        )
    return json.loads(result.stdout)


def test_capacitor_config_ios_content_inset_always():
    try:
        config = _evaluate_capacitor_config()
    except RuntimeError as exc:
        # Fallback: regex-based check on the file contents.
        with open(CAP_CONFIG, "r", encoding="utf-8") as f:
            content = f.read()
        ios_block = re.search(
            r"ios\s*:\s*\{[^{}]*?contentInset\s*:\s*['\"]always['\"]",
            content,
            re.DOTALL,
        )
        assert ios_block is not None, (
            "capacitor.config.ts must configure ios.contentInset = 'always'. "
            f"(Direct evaluation also failed: {exc})"
        )
        return

    assert isinstance(config, dict), (
        "capacitor.config.ts must export an object as the default export."
    )
    ios_cfg = config.get("ios")
    assert isinstance(ios_cfg, dict), (
        f"capacitor.config.ts must have an `ios` config object, got {ios_cfg!r}."
    )
    assert ios_cfg.get("contentInset") == "always", (
        f"ios.contentInset must equal 'always', got {ios_cfg.get('contentInset')!r}."
    )


def test_capacitor_config_preserves_original_fields():
    try:
        config = _evaluate_capacitor_config()
    except RuntimeError:
        with open(CAP_CONFIG, "r", encoding="utf-8") as f:
            content = f.read()
        assert "com.example.myapp" in content, (
            "Original appId 'com.example.myapp' must be preserved."
        )
        assert "My Native App" in content, (
            "Original appName 'My Native App' must be preserved."
        )
        assert re.search(r"webDir\s*:\s*['\"]dist['\"]", content), (
            "Original webDir 'dist' must be preserved."
        )
        return

    assert config.get("appId") == "com.example.myapp", (
        f"appId must remain 'com.example.myapp', got {config.get('appId')!r}."
    )
    assert config.get("appName") == "My Native App", (
        f"appName must remain 'My Native App', got {config.get('appName')!r}."
    )
    assert config.get("webDir") == "dist", (
        f"webDir must remain 'dist', got {config.get('webDir')!r}."
    )
