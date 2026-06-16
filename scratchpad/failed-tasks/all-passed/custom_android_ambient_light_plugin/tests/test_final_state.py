import os
import re
import subprocess

import pytest

PROJECT_DIR = "/home/user/myapp"
ANDROID_DIR = os.path.join(PROJECT_DIR, "android")
ANDROID_APP_SRC = os.path.join(
    ANDROID_DIR, "app", "src", "main", "java", "com", "example", "myapp"
)
PLUGIN_JAVA = os.path.join(ANDROID_APP_SRC, "AmbientLightPlugin.java")
MAIN_ACTIVITY = os.path.join(ANDROID_APP_SRC, "MainActivity.java")
BINDING_TS = os.path.join(PROJECT_DIR, "src", "ambient-light.ts")
DEBUG_APK = os.path.join(
    ANDROID_DIR, "app", "build", "outputs", "apk", "debug", "app-debug.apk"
)


def _strip_comments(src: str) -> str:
    """Remove Java-style line and block comments from source code."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    src = re.sub(r"//[^\n]*", "", src)
    return src


def _extract_method_body(stripped: str, signature_regex: str) -> str:
    """Return the body of a method matching `signature_regex`, including the braces."""
    m = re.search(signature_regex, stripped)
    assert m, (
        f"Could not locate a method matching pattern: {signature_regex!r}"
    )
    # Find the opening brace after the matched signature.
    brace_start = stripped.find("{", m.end() - 1)
    assert brace_start != -1, (
        f"Could not find opening brace for method matching: {signature_regex!r}"
    )
    depth = 0
    end = None
    for i in range(brace_start, len(stripped)):
        c = stripped[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    assert end is not None, (
        f"Could not parse method body braces for: {signature_regex!r}"
    )
    return stripped[brace_start : end + 1]


@pytest.fixture(scope="module")
def plugin_source():
    assert os.path.isfile(PLUGIN_JAVA), (
        f"Expected plugin source at {PLUGIN_JAVA} but it does not exist."
    )
    with open(PLUGIN_JAVA) as f:
        raw = f.read()
    stripped = _strip_comments(raw)
    return {"path": PLUGIN_JAVA, "raw": raw, "src": stripped}


def test_plugin_source_declares_correct_package(plugin_source):
    assert re.search(
        r"^\s*package\s+com\.example\.myapp\s*;",
        plugin_source["src"],
        re.MULTILINE,
    ), "AmbientLightPlugin.java does not declare `package com.example.myapp;` at the top."


def test_plugin_source_has_required_capacitor_imports(plugin_source):
    stripped = plugin_source["src"]
    required_imports = [
        r"com\.getcapacitor\.Plugin",
        r"com\.getcapacitor\.PluginCall",
        r"com\.getcapacitor\.PluginMethod",
        r"com\.getcapacitor\.JSObject",
        r"com\.getcapacitor\.annotation\.CapacitorPlugin",
    ]
    for imp in required_imports:
        assert re.search(rf"import\s+{imp}\s*;", stripped), (
            f"AmbientLightPlugin.java is missing required import for "
            f"{imp.replace(chr(92), '')}."
        )


def test_plugin_source_has_required_android_sensor_imports(plugin_source):
    stripped = plugin_source["src"]
    # Accept either explicit imports of each class or a wildcard `android.hardware.*`.
    wildcard = re.search(r"import\s+android\.hardware\.\*\s*;", stripped)
    required = [
        "android.hardware.Sensor",
        "android.hardware.SensorEvent",
        "android.hardware.SensorEventListener",
        "android.hardware.SensorManager",
    ]
    for fqn in required:
        if wildcard:
            continue
        escaped = re.escape(fqn)
        assert re.search(rf"import\s+{escaped}\s*;", stripped), (
            f"AmbientLightPlugin.java is missing required import for {fqn}. "
            f"(A wildcard `import android.hardware.*;` would also satisfy this.)"
        )


def test_plugin_has_capacitor_plugin_annotation(plugin_source):
    assert re.search(
        r'@CapacitorPlugin\s*\(\s*name\s*=\s*"AmbientLight"\s*\)',
        plugin_source["src"],
    ), (
        "AmbientLightPlugin.java must be annotated with "
        '@CapacitorPlugin(name = "AmbientLight").'
    )


def test_plugin_class_extends_plugin_and_implements_sensor_event_listener(plugin_source):
    stripped = plugin_source["src"]
    m = re.search(
        r"public\s+class\s+AmbientLightPlugin\s+extends\s+Plugin\b([^{]*)\{",
        stripped,
    )
    assert m, (
        "AmbientLightPlugin.java must declare "
        "`public class AmbientLightPlugin extends Plugin`."
    )
    header_tail = m.group(1)
    # The class header may include an `implements <list>` after `extends Plugin`.
    assert re.search(r"\bimplements\b[^{]*\bSensorEventListener\b", header_tail), (
        "AmbientLightPlugin must implement SensorEventListener "
        "(e.g. `extends Plugin implements SensorEventListener`)."
    )


def test_plugin_has_get_light_level_method(plugin_source):
    stripped = plugin_source["src"]
    pattern = (
        r"@PluginMethod(?:\s*\([^)]*\))?\s+"
        r"public\s+void\s+getLightLevel\s*\(\s*PluginCall\s+\w+\s*\)"
    )
    assert re.search(pattern, stripped), (
        "AmbientLightPlugin.java does not declare a @PluginMethod-annotated "
        "`public void getLightLevel(PluginCall ...)` method."
    )


def test_get_light_level_method_puts_value_and_resolves(plugin_source):
    body = _extract_method_body(
        plugin_source["src"],
        r"@PluginMethod(?:\s*\([^)]*\))?\s+"
        r"public\s+void\s+getLightLevel\s*\(\s*PluginCall\s+\w+\s*\)\s*\{",
    )
    assert re.search(r'\.\s*put\s*\(\s*"value"\s*,', body), (
        "getLightLevel() must put the lux reading into a JSObject under "
        'the "value" key (e.g. `ret.put("value", lux)`).'
    )
    assert re.search(r"\bcall\s*\.\s*resolve\s*\(", body), (
        "getLightLevel() must call `call.resolve(ret)` to return the JSObject to JS."
    )


def test_plugin_overrides_handle_on_resume_and_registers_listener(plugin_source):
    body = _extract_method_body(
        plugin_source["src"],
        r"@Override\s+(?:public|protected)\s+void\s+handleOnResume\s*\(\s*\)\s*\{",
    )
    assert re.search(r"\.\s*registerListener\s*\(", body), (
        "handleOnResume() must register a SensorEventListener via "
        "SensorManager.registerListener(...)."
    )


def test_plugin_overrides_handle_on_pause_and_unregisters_listener(plugin_source):
    body = _extract_method_body(
        plugin_source["src"],
        r"@Override\s+(?:public|protected)\s+void\s+handleOnPause\s*\(\s*\)\s*\{",
    )
    assert re.search(r"\.\s*unregisterListener\s*\(", body), (
        "handleOnPause() must unregister the SensorEventListener via "
        "SensorManager.unregisterListener(...)."
    )


def test_plugin_implements_on_sensor_changed_reading_values_zero(plugin_source):
    stripped = plugin_source["src"]
    m = re.search(
        r"public\s+void\s+onSensorChanged\s*\(\s*SensorEvent\s+(\w+)\s*\)\s*\{",
        stripped,
    )
    assert m, (
        "AmbientLightPlugin must implement "
        "`public void onSensorChanged(SensorEvent event)`."
    )
    param_name = m.group(1)
    body = _extract_method_body(
        stripped,
        r"public\s+void\s+onSensorChanged\s*\(\s*SensorEvent\s+\w+\s*\)\s*\{",
    )
    assert re.search(rf"\b{re.escape(param_name)}\s*\.\s*values\s*\[\s*0\s*\]", body), (
        "onSensorChanged() must read the lux reading from "
        f"`{param_name}.values[0]` (the first element of the SensorEvent values array)."
    )


def test_plugin_references_type_light(plugin_source):
    assert re.search(r"\bSensor\s*\.\s*TYPE_LIGHT\b", plugin_source["src"]), (
        "AmbientLightPlugin.java must reference `Sensor.TYPE_LIGHT` to select "
        "the ambient light sensor."
    )


def test_main_activity_registers_ambient_light_plugin():
    assert os.path.isfile(MAIN_ACTIVITY), f"{MAIN_ACTIVITY} does not exist."
    with open(MAIN_ACTIVITY) as f:
        raw = f.read()
    stripped = _strip_comments(raw)

    m = re.search(
        r"void\s+onCreate\s*\(\s*Bundle\s+\w+\s*\)\s*\{",
        stripped,
    )
    assert m, "MainActivity does not declare onCreate(Bundle ...)."

    start = stripped.find("{", m.end() - 1)
    depth = 0
    end = None
    for i in range(start, len(stripped)):
        if stripped[i] == "{":
            depth += 1
        elif stripped[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    assert end is not None, "Could not parse onCreate method body."
    body = stripped[start : end + 1]
    assert re.search(
        r"registerPlugin\s*\(\s*AmbientLightPlugin\s*\.\s*class\s*\)",
        body,
    ), (
        "MainActivity.onCreate must call "
        "registerPlugin(AmbientLightPlugin.class)."
    )


def test_typescript_binding_exists_and_registers_plugin():
    assert os.path.isfile(BINDING_TS), f"{BINDING_TS} does not exist."
    with open(BINDING_TS) as f:
        ts = f.read()

    import_pattern = (
        r"import\s*\{[^}]*\bregisterPlugin\b[^}]*\}\s*from\s*"
        r"['\"]@capacitor/core['\"]"
    )
    assert re.search(import_pattern, ts), (
        "src/ambient-light.ts must import registerPlugin from '@capacitor/core'."
    )

    register_pattern = (
        r"registerPlugin\s*(?:<[^>]*>)?\s*\(\s*['\"]AmbientLight['\"]"
    )
    assert re.search(register_pattern, ts), (
        "src/ambient-light.ts must call registerPlugin with the exact string "
        'literal "AmbientLight".'
    )

    assert re.search(r"export\s+default\s+", ts), (
        "src/ambient-light.ts must have a default export."
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


def test_apk_dex_contains_ambient_light_plugin_class():
    assert os.path.isfile(DEBUG_APK), (
        f"Debug APK {DEBUG_APK} not present; build step must run first."
    )
    descriptor = b"Lcom/example/myapp/AmbientLightPlugin;"

    result = subprocess.run(
        ["unzip", "-p", DEBUG_APK, "classes.dex"],
        capture_output=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"Failed to extract classes.dex from {DEBUG_APK}: "
        f"{result.stderr.decode(errors='ignore')}"
    )
    if descriptor in result.stdout:
        return

    # If the app is multidex, search additional classes*.dex members.
    for idx in range(2, 10):
        member = f"classes{idx}.dex"
        probe = subprocess.run(
            ["unzip", "-p", DEBUG_APK, member],
            capture_output=True,
            timeout=120,
        )
        if probe.returncode != 0 or not probe.stdout:
            continue
        if descriptor in probe.stdout:
            return

    raise AssertionError(
        f"DEX descriptor for plugin class {descriptor.decode()} not found in "
        f"any classes*.dex inside {DEBUG_APK}."
    )
