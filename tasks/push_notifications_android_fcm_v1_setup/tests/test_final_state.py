import json
import os
import re

import pytest

PROJECT_DIR = "/home/user/myproject"
ANDROID_DIR = os.path.join(PROJECT_DIR, "android")
APP_GRADLE = os.path.join(ANDROID_DIR, "app", "build.gradle")
TOP_GRADLE = os.path.join(ANDROID_DIR, "build.gradle")
GOOGLE_SERVICES_JSON = os.path.join(ANDROID_DIR, "app", "google-services.json")
PUSH_TS = os.path.join(PROJECT_DIR, "src", "push.ts")
SETUP_LOG = os.path.join(PROJECT_DIR, "setup.log")
PACKAGE_JSON = os.path.join(PROJECT_DIR, "package.json")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_setup_log_exists_and_contains_required_changes():
    assert os.path.isfile(SETUP_LOG), (
        f"Expected setup log at {SETUP_LOG}. The executor must record applied changes there."
    )
    content = _read(SETUP_LOG)
    required_keywords = {
        "google-services": re.compile(r"^OK:\s*.*google-services", re.MULTILINE),
        "firebase-messaging": re.compile(
            r"^OK:\s*.*firebase-messaging", re.MULTILINE
        ),
        "google-services.json": re.compile(
            r"^OK:\s*.*google-services\.json", re.MULTILINE
        ),
        "requestPermissions": re.compile(
            r"^OK:\s*.*requestPermissions", re.MULTILINE
        ),
    }
    for label, pattern in required_keywords.items():
        assert pattern.search(content), (
            f"setup.log is missing an 'OK: ...' line that mentions '{label}'. "
            f"Current contents:\n{content}"
        )


def test_push_notifications_dependency_added_with_v8():
    assert os.path.isfile(PACKAGE_JSON), f"Missing {PACKAGE_JSON}."
    with open(PACKAGE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    deps = data.get("dependencies") or {}
    assert "@capacitor/push-notifications" in deps, (
        "Expected @capacitor/push-notifications in dependencies of package.json."
    )
    version_spec = deps["@capacitor/push-notifications"]
    match = re.search(r"(\d+)", version_spec)
    assert match is not None, (
        f"Could not parse a numeric major version from "
        f"@capacitor/push-notifications version spec '{version_spec}'."
    )
    major = int(match.group(1))
    assert major == 8, (
        f"Expected @capacitor/push-notifications major version 8, got '{version_spec}'."
    )


def test_top_level_gradle_has_google_services_classpath():
    assert os.path.isfile(TOP_GRADLE), f"Missing {TOP_GRADLE}."
    content = _read(TOP_GRADLE)
    pattern = re.compile(
        r"classpath\s+['\"]com\.google\.gms:google-services:4\.4\.2['\"]"
    )
    assert pattern.search(content), (
        "Expected android/build.gradle to declare a classpath entry for "
        "com.google.gms:google-services:4.4.2. Current contents:\n"
        f"{content}"
    )


def test_app_gradle_applies_google_services_plugin():
    assert os.path.isfile(APP_GRADLE), f"Missing {APP_GRADLE}."
    content = _read(APP_GRADLE)
    legacy = re.compile(
        r"apply\s+plugin\s*:\s*['\"]com\.google\.gms\.google-services['\"]"
    )
    plugins_block = re.compile(
        r"id\s*\(?\s*['\"]com\.google\.gms\.google-services['\"]"
    )
    assert legacy.search(content) or plugins_block.search(content), (
        "Expected android/app/build.gradle to apply the "
        "'com.google.gms.google-services' plugin via either "
        "`apply plugin: 'com.google.gms.google-services'` or a `plugins { id ... }` block."
    )


def test_app_gradle_has_firebase_messaging_dependency():
    content = _read(APP_GRADLE)
    pattern = re.compile(
        r"implementation\s+['\"]com\.google\.firebase:firebase-messaging[^'\"]*['\"]"
    )
    assert pattern.search(content), (
        "Expected android/app/build.gradle to add an implementation dependency on "
        "com.google.firebase:firebase-messaging."
    )


def test_google_services_json_exists_and_is_valid():
    assert os.path.isfile(GOOGLE_SERVICES_JSON), (
        f"Expected placeholder google-services.json at {GOOGLE_SERVICES_JSON}."
    )
    with open(GOOGLE_SERVICES_JSON, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"google-services.json is not valid JSON: {e}")
    clients = data.get("client")
    assert isinstance(clients, list) and len(clients) > 0, (
        "google-services.json must include a non-empty 'client' array."
    )
    matched = False
    for entry in clients:
        try:
            pkg = entry["client_info"]["android_client_info"]["package_name"]
        except (KeyError, TypeError):
            continue
        if pkg == "com.example.myapp":
            matched = True
            break
    assert matched, (
        "google-services.json must include a client whose "
        "client_info.android_client_info.package_name == 'com.example.myapp'."
    )


def test_push_ts_imports_plugin_and_exports_init_push():
    assert os.path.isfile(PUSH_TS), f"Missing TypeScript wiring file at {PUSH_TS}."
    content = _read(PUSH_TS)
    import_pattern = re.compile(
        r"import\s*\{[^}]*\bPushNotifications\b[^}]*\}\s*from\s*['\"]@capacitor/push-notifications['\"]"
    )
    assert import_pattern.search(content), (
        "Expected src/push.ts to import { PushNotifications } from '@capacitor/push-notifications'."
    )
    export_pattern = re.compile(
        r"export\s+(?:async\s+)?(?:function\s+initPush\b|const\s+initPush\b|let\s+initPush\b)"
    )
    assert export_pattern.search(content), (
        "Expected src/push.ts to export a symbol named `initPush` "
        "(via `export function initPush`, `export async function initPush`, or `export const initPush`)."
    )


def test_push_ts_registers_all_four_event_listeners():
    content = _read(PUSH_TS)
    required_events = [
        "registration",
        "registrationError",
        "pushNotificationReceived",
        "pushNotificationActionPerformed",
    ]
    for event in required_events:
        pattern = re.compile(rf"['\"]{re.escape(event)}['\"]")
        assert pattern.search(content), (
            f"src/push.ts must reference the event name literal '{event}' "
            "(used in PushNotifications.addListener call)."
        )


def test_push_ts_requests_permissions_before_register_and_guards_on_granted():
    content = _read(PUSH_TS)
    req_match = re.search(r"requestPermissions\s*\(", content)
    reg_match = re.search(r"\bregister\s*\(\s*\)", content)
    assert req_match is not None, (
        "src/push.ts must call PushNotifications.requestPermissions()."
    )
    assert reg_match is not None, (
        "src/push.ts must call PushNotifications.register()."
    )
    assert req_match.start() < reg_match.start(), (
        "PushNotifications.requestPermissions() must be called before PushNotifications.register()."
    )
    between = content[req_match.end(): reg_match.start()]
    granted_pattern = re.compile(r"['\"]granted['\"]")
    assert granted_pattern.search(between), (
        "register() must be guarded by a check against the 'granted' permission state — "
        "the string literal 'granted' must appear between requestPermissions() and register()."
    )
