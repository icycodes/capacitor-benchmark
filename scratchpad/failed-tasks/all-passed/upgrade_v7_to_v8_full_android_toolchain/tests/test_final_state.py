import json
import os
import re

PROJECT_DIR = "/home/user/myapp"


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _satisfies_caret_major(spec: str, expected_major: int) -> bool:
    """Return True iff `spec` resolves to the requested major. Accepts forms like
    `8`, `8.0.0`, `^8.0.0`, `~8.1.2`, `8.x`, etc. Rejects ranges/disjunctions."""
    s = spec.strip()
    if " " in s or "||" in s or " - " in s:
        return False
    m = re.match(r"^[~^]?v?(\d+)(?:\.[\d]+|\.x|\.\*)?(?:\.[\d]+|\.x|\.\*)?", s)
    if not m:
        return False
    return int(m.group(1)) == expected_major


def test_log_file_exists_and_has_success_marker():
    log_path = os.path.join(PROJECT_DIR, "upgrade.log")
    assert os.path.isfile(log_path), (
        f"Expected the executor to write the cap sync output to {log_path}."
    )
    content = _read(log_path)
    assert "Sync finished" in content, (
        "upgrade.log must contain the marker 'Sync finished' to prove "
        "`npx cap sync android` completed successfully."
    )


def test_package_json_declares_capacitor_v8():
    pkg = json.loads(_read(os.path.join(PROJECT_DIR, "package.json")))
    deps = {}
    deps.update(pkg.get("dependencies", {}) or {})
    deps.update(pkg.get("devDependencies", {}) or {})
    for name in ("@capacitor/core", "@capacitor/cli", "@capacitor/android"):
        assert name in deps, f"{name} should still be declared in package.json after the upgrade."
        spec = deps[name]
        assert _satisfies_caret_major(spec, 8), (
            f"Expected {name} to resolve to the 8.x major after upgrade, got {spec!r}."
        )


def test_installed_capacitor_core_is_v8():
    installed_pkg = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "core", "package.json")
    assert os.path.isfile(installed_pkg), (
        f"{installed_pkg} is missing — `npm install` after the upgrade did not run successfully."
    )
    meta = json.loads(_read(installed_pkg))
    version = meta.get("version", "")
    assert version.startswith("8."), (
        f"Installed @capacitor/core version must be 8.x, got {version!r}."
    )


def test_android_build_gradle_uses_agp_8_7_x():
    content = _read(os.path.join(PROJECT_DIR, "android", "build.gradle"))
    assert re.search(
        r"com\.android\.tools\.build:gradle:8\.7\.\d+", content
    ), (
        "android/build.gradle must reference Android Gradle Plugin 8.7.x "
        "(e.g. `com.android.tools.build:gradle:8.7.3`)."
    )


def test_gradle_wrapper_uses_gradle_8_11_x():
    content = _read(
        os.path.join(PROJECT_DIR, "android", "gradle", "wrapper", "gradle-wrapper.properties")
    )
    assert re.search(
        r"distributionUrl=.*gradle-8\.11\.\d+(-all|-bin)\.zip", content
    ), (
        "gradle-wrapper.properties must point distributionUrl at a Gradle 8.11.x "
        "distribution (e.g. gradle-8.11.1-all.zip)."
    )


def test_variables_gradle_sdk_and_kotlin():
    content = _read(os.path.join(PROJECT_DIR, "android", "variables.gradle"))
    assert re.search(r"compileSdkVersion\s*=\s*35\b", content), (
        "variables.gradle must set compileSdkVersion = 35."
    )
    assert re.search(r"targetSdkVersion\s*=\s*35\b", content), (
        "variables.gradle must set targetSdkVersion = 35."
    )
    assert re.search(r"kotlin_version\s*=\s*['\"]2\.0\.21['\"]", content), (
        "variables.gradle must set kotlin_version = '2.0.21'."
    )


def test_main_activity_still_extends_bridge_activity():
    main_activity_path = os.path.join(
        PROJECT_DIR,
        "android",
        "app",
        "src",
        "main",
        "java",
        "com",
        "example",
        "myapp",
        "MainActivity.java",
    )
    content = _read(main_activity_path)
    assert "import com.getcapacitor.BridgeActivity" in content, (
        "MainActivity.java must still import com.getcapacitor.BridgeActivity for v8."
    )
    assert re.search(
        r"class\s+MainActivity\s+extends\s+BridgeActivity", content
    ), "MainActivity must remain a subclass of BridgeActivity."
