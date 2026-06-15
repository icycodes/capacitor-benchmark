import os
import re
import subprocess

import pytest

PROJECT_DIR = "/home/user/myapp"
ANDROID_DIR = os.path.join(PROJECT_DIR, "android")
ANDROID_APP_SRC = os.path.join(
    ANDROID_DIR, "app", "src", "main", "java", "com", "example", "myapp"
)
DEBUG_APK = os.path.join(
    ANDROID_DIR, "app", "build", "outputs", "apk", "debug", "app-debug.apk"
)


def _strip_comments(src: str) -> str:
    """Remove Java-style line and block comments from source code."""
    # Remove block comments first, then line comments.
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    src = re.sub(r"//[^\n]*", "", src)
    return src


def _find_plugin_source():
    """Locate the executor-authored plugin Java source file. Returns (path, source)."""
    assert os.path.isdir(ANDROID_APP_SRC), (
        f"{ANDROID_APP_SRC} is missing. The Android source tree was destroyed?"
    )
    java_files = [
        f
        for f in os.listdir(ANDROID_APP_SRC)
        if f.endswith(".java") and f != "MainActivity.java"
    ]
    candidates = []
    for fname in java_files:
        path = os.path.join(ANDROID_APP_SRC, fname)
        with open(path) as f:
            src = f.read()
        stripped = _strip_comments(src)
        if re.search(
            r'@CapacitorPlugin\s*\(\s*name\s*=\s*"DeviceSensor"\s*\)', stripped
        ):
            candidates.append((path, src, stripped))
    assert candidates, (
        "No Java file with the annotation @CapacitorPlugin(name = \"DeviceSensor\") "
        f"was found under {ANDROID_APP_SRC}."
    )
    assert len(candidates) == 1, (
        f"Expected exactly one plugin source, found {len(candidates)}: "
        f"{[c[0] for c in candidates]}"
    )
    return candidates[0]


@pytest.fixture(scope="module")
def plugin_source():
    path, src, stripped = _find_plugin_source()
    return {"path": path, "raw": src, "src": stripped}


@pytest.fixture(scope="module")
def plugin_class_name(plugin_source):
    stripped = plugin_source["src"]
    m = re.search(
        r"public\s+class\s+([A-Za-z_][A-Za-z0-9_]*)\s+extends\s+Plugin\b",
        stripped,
    )
    assert m, (
        "The plugin source does not declare `public class <Name> extends Plugin`."
    )
    return m.group(1)


def test_plugin_source_declares_correct_package(plugin_source):
    assert re.search(
        r"^\s*package\s+com\.example\.myapp\s*;",
        plugin_source["src"],
        re.MULTILINE,
    ), (
        "Plugin source does not declare `package com.example.myapp;` at the top."
    )


def test_plugin_source_has_required_imports(plugin_source):
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
            f"Plugin source is missing required import for {imp.replace(chr(92), '')}."
        )


def test_plugin_class_extends_plugin(plugin_class_name):
    assert plugin_class_name, "Plugin class name could not be identified."


def test_plugin_has_get_reading_method(plugin_source):
    stripped = plugin_source["src"]
    pattern = (
        r"@PluginMethod(?:\s*\([^)]*\))?\s+"
        r"public\s+void\s+getReading\s*\(\s*PluginCall\s+\w+\s*\)"
    )
    assert re.search(pattern, stripped), (
        "Plugin source does not declare a @PluginMethod-annotated "
        "`public void getReading(PluginCall ...)` method."
    )


def test_plugin_has_is_available_method(plugin_source):
    stripped = plugin_source["src"]
    pattern = (
        r"@PluginMethod(?:\s*\([^)]*\))?\s+"
        r"public\s+void\s+isAvailable\s*\(\s*PluginCall\s+\w+\s*\)"
    )
    assert re.search(pattern, stripped), (
        "Plugin source does not declare a @PluginMethod-annotated "
        "`public void isAvailable(PluginCall ...)` method."
    )


def test_plugin_has_reject_call(plugin_source):
    assert re.search(r"\.reject\s*\(", plugin_source["src"]), (
        "Plugin source must contain at least one PluginCall.reject(...) "
        "call to handle unknown sensors."
    )


@pytest.mark.parametrize(
    "sensor,value,unit",
    [
        ("temperature", "22.5", "C"),
        ("humidity", "65.0", "%"),
        ("battery", "87.0", "%"),
    ],
)
def test_plugin_has_correct_value_for_sensor(plugin_source, sensor, value, unit):
    """For each supported sensor, the value and unit literals must appear close to
    the sensor name literal in the plugin source."""
    src = plugin_source["src"]
    sensor_literal = f'"{sensor}"'
    idx = src.find(sensor_literal)
    assert idx != -1, (
        f"Plugin source does not mention the sensor literal {sensor_literal}."
    )
    window = src[idx : idx + 800]
    assert value in window, (
        f"Expected literal value {value} for sensor '{sensor}' within 800 "
        f"characters of the sensor literal."
    )
    assert f'"{unit}"' in window, (
        f'Expected literal unit "{unit}" for sensor \'{sensor}\' within 800 '
        f"characters of the sensor literal."
    )


def test_main_activity_registers_plugin(plugin_class_name):
    main_activity = os.path.join(ANDROID_APP_SRC, "MainActivity.java")
    assert os.path.isfile(main_activity), f"{main_activity} does not exist."
    with open(main_activity) as f:
        src = f.read()
    stripped = _strip_comments(src)

    # Find onCreate body and ensure registerPlugin(<PluginClass>.class) is inside it.
    m = re.search(
        r"void\s+onCreate\s*\(\s*Bundle\s+\w+\s*\)\s*\{", stripped
    )
    assert m, "MainActivity does not declare onCreate(Bundle ...)."
    # Walk braces to find matching close.
    start = m.end() - 1  # the '{'
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
    pattern = rf"registerPlugin\s*\(\s*{re.escape(plugin_class_name)}\s*\.\s*class\s*\)"
    assert re.search(pattern, body), (
        f"MainActivity.onCreate does not call registerPlugin({plugin_class_name}.class)."
    )


def test_typescript_binding_exists_and_registers_plugin():
    binding = os.path.join(PROJECT_DIR, "src", "device-sensor.ts")
    assert os.path.isfile(binding), f"{binding} does not exist."
    with open(binding) as f:
        ts = f.read()

    # registerPlugin import from @capacitor/core
    import_pattern = (
        r"import\s*\{[^}]*\bregisterPlugin\b[^}]*\}\s*from\s*['\"]@capacitor/core['\"]"
    )
    assert re.search(import_pattern, ts), (
        "device-sensor.ts must import registerPlugin from '@capacitor/core'."
    )

    # registerPlugin("DeviceSensor"...)
    register_pattern = (
        r"registerPlugin\s*(?:<[^>]*>)?\s*\(\s*['\"]DeviceSensor['\"]"
    )
    m = re.search(register_pattern, ts)
    assert m, (
        "device-sensor.ts must call registerPlugin with the exact string literal "
        '"DeviceSensor".'
    )

    # default export of the registered plugin object.
    # Accept either "export default <ident>;" or "export default registerPlugin(...)".
    assert re.search(r"export\s+default\s+", ts), (
        "device-sensor.ts must have a default export."
    )


def test_gradle_build_succeeds_and_apk_exists():
    # Remove stale APK first so the test exercises a fresh build.
    if os.path.exists(DEBUG_APK):
        os.remove(DEBUG_APK)
    env = os.environ.copy()
    # Make sure Java and Android SDK env vars propagate.
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


def test_apk_dex_contains_plugin_class(plugin_class_name):
    assert os.path.isfile(DEBUG_APK), (
        f"Debug APK {DEBUG_APK} not present; build step must run first."
    )
    # Extract classes.dex from the APK in-memory and search for the plugin descriptor.
    result = subprocess.run(
        ["unzip", "-p", DEBUG_APK, "classes.dex"],
        capture_output=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"Failed to extract classes.dex from {DEBUG_APK}: {result.stderr.decode(errors='ignore')}"
    )
    dex_bytes = result.stdout
    descriptor = f"Lcom/example/myapp/{plugin_class_name};".encode("utf-8")
    if descriptor in dex_bytes:
        return

    # Some apps may split into multiple dex files; try classes2.dex, classes3.dex...
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
        f"DEX descriptor for plugin class {descriptor.decode()} not found in any "
        f"classes*.dex inside {DEBUG_APK}."
    )
