import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET

import pytest

PROJECT_DIR = "/home/user/myapp"
ANDROID_DIR = os.path.join(PROJECT_DIR, "android")
ANDROID_MANIFEST = os.path.join(
    ANDROID_DIR, "app", "src", "main", "AndroidManifest.xml"
)
ASSETLINKS_PATH = os.path.join(PROJECT_DIR, ".well-known", "assetlinks.json")
DEEPLINK_TS = os.path.join(PROJECT_DIR, "src", "deeplink.ts")
PACKAGE_JSON = os.path.join(PROJECT_DIR, "package.json")
DEBUG_KEYSTORE = os.path.expanduser("~/.android/debug.keystore")
DEBUG_APK = os.path.join(
    ANDROID_DIR, "app", "build", "outputs", "apk", "debug", "app-debug.apk"
)

ANDROID_NS = "http://schemas.android.com/apk/res/android"
ANDROID_NAME = f"{{{ANDROID_NS}}}name"
ANDROID_AUTOVERIFY = f"{{{ANDROID_NS}}}autoVerify"
ANDROID_SCHEME = f"{{{ANDROID_NS}}}scheme"
ANDROID_HOST = f"{{{ANDROID_NS}}}host"
ANDROID_PATH_PREFIX = f"{{{ANDROID_NS}}}pathPrefix"
ANDROID_PATH_PATTERN = f"{{{ANDROID_NS}}}pathPattern"
ANDROID_PATH = f"{{{ANDROID_NS}}}path"


def _normalize_fingerprint(value: str) -> str:
    """Uppercase and strip whitespace from a SHA-256 fingerprint string."""
    return re.sub(r"\s+", "", value).upper()


@pytest.fixture(scope="module")
def expected_sha256_fingerprint():
    assert os.path.isfile(DEBUG_KEYSTORE), (
        f"Debug keystore {DEBUG_KEYSTORE} does not exist; cannot verify fingerprint."
    )
    result = subprocess.run(
        [
            "keytool",
            "-list",
            "-v",
            "-alias",
            "androiddebugkey",
            "-keystore",
            DEBUG_KEYSTORE,
            "-storepass",
            "android",
            "-keypass",
            "android",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"keytool failed to list the debug keystore: {result.stderr}"
    )
    # Look for the SHA256 line (e.g. "SHA256: AA:BB:CC:...").
    m = re.search(r"SHA256:\s*([0-9A-Fa-f:]+)", result.stdout)
    assert m, (
        "Could not locate SHA256 fingerprint in keytool output. Full output:\n"
        f"{result.stdout}"
    )
    return _normalize_fingerprint(m.group(1))


@pytest.fixture(scope="module")
def main_activity_element():
    assert os.path.isfile(ANDROID_MANIFEST), (
        f"AndroidManifest.xml not found at {ANDROID_MANIFEST}."
    )
    tree = ET.parse(ANDROID_MANIFEST)
    root = tree.getroot()
    application = root.find("application")
    assert application is not None, "AndroidManifest.xml has no <application> element."
    main_activity = None
    for activity in application.findall("activity"):
        name = activity.get(ANDROID_NAME, "")
        if name in (".MainActivity", "com.example.myapp.MainActivity"):
            main_activity = activity
            break
    assert main_activity is not None, (
        "AndroidManifest.xml does not contain an <activity android:name=\".MainActivity\"> "
        "element."
    )
    return main_activity


def test_manifest_still_has_main_launcher_filter(main_activity_element):
    """The pre-existing MAIN/LAUNCHER intent filter must be preserved."""
    found_main_launcher = False
    for intent_filter in main_activity_element.findall("intent-filter"):
        actions = [a.get(ANDROID_NAME) for a in intent_filter.findall("action")]
        categories = [c.get(ANDROID_NAME) for c in intent_filter.findall("category")]
        if (
            "android.intent.action.MAIN" in actions
            and "android.intent.category.LAUNCHER" in categories
        ):
            found_main_launcher = True
            break
    assert found_main_launcher, (
        "The original MAIN/LAUNCHER intent filter on MainActivity must remain in place; "
        "it could not be found in AndroidManifest.xml."
    )


def test_manifest_declares_app_link_intent_filter(main_activity_element):
    """An additional App-Link intent filter must be declared on MainActivity."""
    matching_filter = None
    for intent_filter in main_activity_element.findall("intent-filter"):
        if intent_filter.get(ANDROID_AUTOVERIFY) != "true":
            continue
        actions = [a.get(ANDROID_NAME) for a in intent_filter.findall("action")]
        categories = [c.get(ANDROID_NAME) for c in intent_filter.findall("category")]
        if "android.intent.action.VIEW" not in actions:
            continue
        if "android.intent.category.DEFAULT" not in categories:
            continue
        if "android.intent.category.BROWSABLE" not in categories:
            continue

        data_elements = intent_filter.findall("data")
        if not data_elements:
            continue

        # Across all <data> children of this filter, scheme=https and host=myapp.example.com
        # must both be declared (Android merges all <data> children of a single
        # intent filter into the combinatorial product).
        schemes = {d.get(ANDROID_SCHEME) for d in data_elements if d.get(ANDROID_SCHEME)}
        hosts = {d.get(ANDROID_HOST) for d in data_elements if d.get(ANDROID_HOST)}
        if "https" not in schemes:
            continue
        if "myapp.example.com" not in hosts:
            continue

        # At least one <data> child must restrict the path to /.well-known/.
        path_ok = False
        for d in data_elements:
            prefix = d.get(ANDROID_PATH_PREFIX)
            pattern = d.get(ANDROID_PATH_PATTERN)
            path_val = d.get(ANDROID_PATH)
            if prefix is not None and prefix.rstrip("/") == "/.well-known":
                path_ok = True
                break
            if pattern is not None and pattern.startswith("/.well-known"):
                path_ok = True
                break
            if path_val is not None and path_val.startswith("/.well-known"):
                path_ok = True
                break
        if not path_ok:
            continue

        matching_filter = intent_filter
        break

    assert matching_filter is not None, (
        "MainActivity must contain an <intent-filter android:autoVerify=\"true\"> with "
        "the VIEW action, DEFAULT + BROWSABLE categories, scheme=https, "
        "host=myapp.example.com, and a path constraint that covers /.well-known/ "
        "(android:pathPrefix=\"/.well-known\" or android:pathPattern=\"/.well-known/.*\")."
    )


def test_assetlinks_json_exists_and_is_valid_json():
    assert os.path.isfile(ASSETLINKS_PATH), (
        f"Digital Asset Links file {ASSETLINKS_PATH} does not exist."
    )
    with open(ASSETLINKS_PATH) as f:
        data = json.load(f)
    assert isinstance(data, list) and len(data) >= 1, (
        f"{ASSETLINKS_PATH} must be a non-empty JSON array of statement objects."
    )


def _qualifying_statements():
    with open(ASSETLINKS_PATH) as f:
        data = json.load(f)
    qualifying = []
    for stmt in data:
        if not isinstance(stmt, dict):
            continue
        relation = stmt.get("relation")
        target = stmt.get("target")
        if not isinstance(relation, list) or not isinstance(target, dict):
            continue
        if "delegate_permission/common.handle_all_urls" not in relation:
            continue
        if target.get("namespace") != "android_app":
            continue
        if target.get("package_name") != "com.example.myapp":
            continue
        fps = target.get("sha256_cert_fingerprints")
        if not isinstance(fps, list) or not fps:
            continue
        if not all(isinstance(fp, str) and fp.strip() for fp in fps):
            continue
        qualifying.append(stmt)
    return qualifying


def test_assetlinks_json_has_qualifying_statement():
    qualifying = _qualifying_statements()
    assert qualifying, (
        f"{ASSETLINKS_PATH} must contain at least one statement with "
        "relation 'delegate_permission/common.handle_all_urls', target.namespace "
        "'android_app', target.package_name 'com.example.myapp', and a non-empty "
        "target.sha256_cert_fingerprints array."
    )


def test_assetlinks_json_fingerprint_matches_debug_keystore(expected_sha256_fingerprint):
    qualifying = _qualifying_statements()
    assert qualifying, (
        "Cannot verify the fingerprint because there is no qualifying statement "
        f"in {ASSETLINKS_PATH}."
    )
    seen = []
    for stmt in qualifying:
        for fp in stmt["target"]["sha256_cert_fingerprints"]:
            normalized = _normalize_fingerprint(fp)
            seen.append(normalized)
            if normalized == expected_sha256_fingerprint:
                return
    raise AssertionError(
        "None of the SHA-256 fingerprints in assetlinks.json match the debug keystore. "
        f"Expected (normalized): {expected_sha256_fingerprint}. "
        f"Found (normalized): {seen}."
    )


@pytest.fixture(scope="module")
def deeplink_source():
    assert os.path.isfile(DEEPLINK_TS), f"{DEEPLINK_TS} does not exist."
    with open(DEEPLINK_TS) as f:
        return f.read()


def test_deeplink_ts_imports_app_from_capacitor_app(deeplink_source):
    pattern = (
        r"import\s*\{[^}]*\bApp\b[^}]*\}\s*from\s*"
        r"['\"]@capacitor/app['\"]"
    )
    assert re.search(pattern, deeplink_source), (
        "src/deeplink.ts must contain a named import of `App` from '@capacitor/app'."
    )


def test_deeplink_ts_registers_app_url_open_listener(deeplink_source):
    pattern = (
        r"App\s*\.\s*addListener\s*\(\s*['\"]appUrlOpen['\"]"
    )
    assert re.search(pattern, deeplink_source), (
        "src/deeplink.ts must call `App.addListener('appUrlOpen', ...)`."
    )


def test_deeplink_ts_parses_url(deeplink_source):
    assert re.search(r"\bnew\s+URL\s*\(", deeplink_source), (
        "src/deeplink.ts must use `new URL(...)` to parse the incoming URL."
    )


def test_deeplink_ts_invokes_spa_routing_api(deeplink_source):
    routing_apis = [
        r"window\s*\.\s*location\s*\.\s*replace\s*\(",
        r"window\s*\.\s*location\s*\.\s*assign\s*\(",
        r"window\s*\.\s*location\s*\.\s*href\s*=",
        r"window\s*\.\s*history\s*\.\s*replaceState\s*\(",
        r"window\s*\.\s*history\s*\.\s*pushState\s*\(",
    ]
    assert any(re.search(p, deeplink_source) for p in routing_apis), (
        "src/deeplink.ts must invoke one of window.location.replace/assign, "
        "set window.location.href, or call window.history.replaceState/pushState "
        "to drive SPA routing."
    )


def test_deeplink_ts_exports_registration_function(deeplink_source):
    patterns = [
        r"export\s+default\s+",
        r"export\s+function\s+\w+\s*\(",
        r"export\s+const\s+\w+\s*=",
        r"export\s+let\s+\w+\s*=",
        r"export\s+\{\s*\w+",
        r"export\s+async\s+function\s+\w+\s*\(",
    ]
    assert any(re.search(p, deeplink_source) for p in patterns), (
        "src/deeplink.ts must export the registration function via a named export "
        "or a default export."
    )


def test_package_json_still_has_capacitor_app():
    assert os.path.isfile(PACKAGE_JSON), f"{PACKAGE_JSON} does not exist."
    with open(PACKAGE_JSON) as f:
        pkg = json.load(f)
    deps = pkg.get("dependencies", {})
    value = deps.get("@capacitor/app")
    assert isinstance(value, str) and value.strip(), (
        "package.json dependencies['@capacitor/app'] must remain a non-empty string."
    )


def test_gradle_build_succeeds_and_apk_exists():
    if os.path.exists(DEBUG_APK):
        os.remove(DEBUG_APK)
    env = os.environ.copy()
    result = subprocess.run(
        ["./gradlew", ":app:assembleDebug", "--offline", "-q"],
        cwd=ANDROID_DIR,
        capture_output=True,
        text=True,
        env=env,
        timeout=900,
    )
    if result.returncode != 0:
        # Retry once without --offline to recover from any transient cache miss.
        result = subprocess.run(
            ["./gradlew", ":app:assembleDebug", "-q"],
            cwd=ANDROID_DIR,
            capture_output=True,
            text=True,
            env=env,
            timeout=1200,
        )
    assert result.returncode == 0, (
        f"Gradle build failed (exit={result.returncode}).\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    assert os.path.isfile(DEBUG_APK), (
        f"Expected debug APK at {DEBUG_APK} but it does not exist."
    )
