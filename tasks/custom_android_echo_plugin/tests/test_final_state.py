import os
import re
import subprocess

import pytest

PROJECT_DIR = "/home/user/myapp"
ANDROID_DIR = os.path.join(PROJECT_DIR, "android")
ANDROID_APP_SRC = os.path.join(
    ANDROID_DIR, "app", "src", "main", "java", "com", "example", "myapp"
)
PLUGIN_JAVA = os.path.join(ANDROID_APP_SRC, "EchoPlugin.java")
MAIN_ACTIVITY = os.path.join(ANDROID_APP_SRC, "MainActivity.java")
ECHO_TS = os.path.join(PROJECT_DIR, "src", "echo.ts")
DEBUG_APK = os.path.join(
    ANDROID_DIR, "app", "build", "outputs", "apk", "debug", "app-debug.apk"
)


def _strip_comments(src: str) -> str:
    """Remove Java-style line and block comments from source code."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    src = re.sub(r"//[^\n]*", "", src)
    return src


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
    ), "EchoPlugin.java does not declare `package com.example.myapp;` at the top."


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
            f"EchoPlugin.java is missing required import for "
            f"{imp.replace(chr(92), '')}."
        )


def test_plugin_has_capacitor_plugin_annotation(plugin_source):
    assert re.search(
        r'@CapacitorPlugin\s*\(\s*name\s*=\s*"Echo"\s*\)',
        plugin_source["src"],
    ), (
        "EchoPlugin.java must be annotated with "
        "@CapacitorPlugin(name = \"Echo\")."
    )


def test_plugin_class_extends_plugin(plugin_source):
    assert re.search(
        r"public\s+class\s+EchoPlugin\s+extends\s+Plugin\b",
        plugin_source["src"],
    ), "EchoPlugin.java must declare `public class EchoPlugin extends Plugin`."


def test_plugin_has_echo_method(plugin_source):
    stripped = plugin_source["src"]
    pattern = (
        r"@PluginMethod(?:\s*\([^)]*\))?\s+"
        r"public\s+void\s+echo\s*\(\s*PluginCall\s+\w+\s*\)"
    )
    assert re.search(pattern, stripped), (
        "EchoPlugin.java does not declare a @PluginMethod-annotated "
        "`public void echo(PluginCall ...)` method."
    )


def _extract_echo_body(stripped: str) -> str:
    """Return the body of the `echo` method, including the braces."""
    m = re.search(
        r"@PluginMethod(?:\s*\([^)]*\))?\s+"
        r"public\s+void\s+echo\s*\(\s*PluginCall\s+\w+\s*\)\s*\{",
        stripped,
    )
    assert m, "Could not locate the echo() method signature."
    start = m.end() - 1  # the '{'
    depth = 0
    end = None
    for i in range(start, len(stripped)):
        c = stripped[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    assert end is not None, "Could not parse echo() method body braces."
    return stripped[start : end + 1]


def test_echo_method_uses_call_get_string_value(plugin_source):
    body = _extract_echo_body(plugin_source["src"])
    assert re.search(r'\.\s*getString\s*\(\s*"value"\s*\)', body), (
        'echo() must call `call.getString("value")` to read the input string.'
    )


def test_echo_method_puts_value_into_jsobject(plugin_source):
    body = _extract_echo_body(plugin_source["src"])
    # match either `<ident>.put("value", ...)` or `new JSObject().put("value", ...)`.
    assert re.search(r'\.\s*put\s*\(\s*"value"\s*,', body), (
        'echo() must put the result into a JSObject under the "value" key '
        '(e.g. `ret.put("value", value)`).'
    )


def test_echo_method_calls_resolve(plugin_source):
    body = _extract_echo_body(plugin_source["src"])
    assert re.search(r"\bcall\s*\.\s*resolve\s*\(", body), (
        "echo() must call `call.resolve(ret)` to return the JSObject to JS."
    )


def test_main_activity_registers_echo_plugin():
    assert os.path.isfile(MAIN_ACTIVITY), f"{MAIN_ACTIVITY} does not exist."
    with open(MAIN_ACTIVITY) as f:
        raw = f.read()
    stripped = _strip_comments(raw)

    m = re.search(
        r"void\s+onCreate\s*\(\s*Bundle\s+\w+\s*\)\s*\{",
        stripped,
    )
    assert m, "MainActivity does not declare onCreate(Bundle ...)."

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
    assert re.search(
        r"registerPlugin\s*\(\s*EchoPlugin\s*\.\s*class\s*\)",
        body,
    ), "MainActivity.onCreate must call registerPlugin(EchoPlugin.class)."


def test_typescript_binding_exists_and_registers_plugin():
    assert os.path.isfile(ECHO_TS), f"{ECHO_TS} does not exist."
    with open(ECHO_TS) as f:
        ts = f.read()

    import_pattern = (
        r"import\s*\{[^}]*\bregisterPlugin\b[^}]*\}\s*from\s*"
        r"['\"]@capacitor/core['\"]"
    )
    assert re.search(import_pattern, ts), (
        "src/echo.ts must import registerPlugin from '@capacitor/core'."
    )

    register_pattern = (
        r"registerPlugin\s*(?:<[^>]*>)?\s*\(\s*['\"]Echo['\"]"
    )
    assert re.search(register_pattern, ts), (
        "src/echo.ts must call registerPlugin with the exact string literal "
        '"Echo".'
    )

    assert re.search(r"export\s+default\s+", ts), (
        "src/echo.ts must have a default export."
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


def test_apk_dex_contains_echo_plugin_class():
    assert os.path.isfile(DEBUG_APK), (
        f"Debug APK {DEBUG_APK} not present; build step must run first."
    )
    descriptor = b"Lcom/example/myapp/EchoPlugin;"

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
