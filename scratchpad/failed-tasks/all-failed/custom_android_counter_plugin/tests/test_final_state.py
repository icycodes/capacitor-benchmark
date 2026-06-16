import os
import re
import subprocess

import pytest

PROJECT_DIR = "/home/user/myapp"
ANDROID_DIR = os.path.join(PROJECT_DIR, "android")
ANDROID_APP_SRC = os.path.join(
    ANDROID_DIR, "app", "src", "main", "java", "com", "example", "myapp"
)
PLUGIN_PATH = os.path.join(ANDROID_APP_SRC, "CounterPlugin.java")
DEBUG_APK = os.path.join(
    ANDROID_DIR, "app", "build", "outputs", "apk", "debug", "app-debug.apk"
)


def _strip_comments(src: str) -> str:
    """Remove Java-style line and block comments from source code."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    src = re.sub(r"//[^\n]*", "", src)
    return src


def _extract_method_body(src: str, method_name: str) -> str | None:
    """Extract the body of a @PluginMethod-annotated method `method_name` from
    a comment-stripped Java source string. Returns None if not found."""
    pattern = (
        rf"@PluginMethod(?:\s*\([^)]*\))?\s+"
        rf"public\s+void\s+{re.escape(method_name)}\s*\(\s*PluginCall\s+\w+\s*\)\s*\{{"
    )
    m = re.search(pattern, src)
    if not m:
        return None
    start = m.end() - 1  # the '{'
    depth = 0
    for i in range(start, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[start : i + 1]
    return None


@pytest.fixture(scope="module")
def plugin_source():
    assert os.path.isfile(PLUGIN_PATH), (
        f"Plugin source file {PLUGIN_PATH} does not exist."
    )
    with open(PLUGIN_PATH) as f:
        raw = f.read()
    return {"path": PLUGIN_PATH, "raw": raw, "src": _strip_comments(raw)}


def test_plugin_source_declares_correct_package(plugin_source):
    assert re.search(
        r"^\s*package\s+com\.example\.myapp\s*;",
        plugin_source["src"],
        re.MULTILINE,
    ), "CounterPlugin.java does not declare `package com.example.myapp;` at the top."


def test_plugin_source_has_required_imports(plugin_source):
    stripped = plugin_source["src"]
    required_imports = [
        r"com\.getcapacitor\.Plugin",
        r"com\.getcapacitor\.PluginCall",
        r"com\.getcapacitor\.PluginMethod",
        r"com\.getcapacitor\.JSObject",
        r"com\.getcapacitor\.annotation\.CapacitorPlugin",
        r"java\.util\.concurrent\.atomic\.AtomicInteger",
    ]
    for imp in required_imports:
        assert re.search(rf"import\s+{imp}\s*;", stripped), (
            f"CounterPlugin.java is missing required import for "
            f"{imp.replace(chr(92), '')}."
        )


def test_plugin_has_capacitor_plugin_annotation(plugin_source):
    assert re.search(
        r'@CapacitorPlugin\s*\(\s*name\s*=\s*"Counter"\s*\)',
        plugin_source["src"],
    ), (
        'CounterPlugin.java must be annotated with @CapacitorPlugin(name = "Counter").'
    )


def test_plugin_class_extends_plugin(plugin_source):
    assert re.search(
        r"public\s+class\s+CounterPlugin\s+extends\s+Plugin\b",
        plugin_source["src"],
    ), "CounterPlugin.java must declare `public class CounterPlugin extends Plugin`."


def test_plugin_has_private_final_atomic_integer_field(plugin_source):
    pattern = (
        r"private\s+final\s+AtomicInteger\s+\w+\s*=\s*new\s+AtomicInteger\s*\(\s*0\s*\)\s*;"
    )
    assert re.search(pattern, plugin_source["src"]), (
        "CounterPlugin.java must declare a `private final AtomicInteger` field "
        "initialized to `new AtomicInteger(0)`."
    )


@pytest.mark.parametrize("method_name", ["increment", "decrement", "get"])
def test_plugin_has_plugin_method(plugin_source, method_name):
    body = _extract_method_body(plugin_source["src"], method_name)
    assert body is not None, (
        f"CounterPlugin.java does not declare a @PluginMethod-annotated "
        f"`public void {method_name}(PluginCall ...)` method."
    )


@pytest.mark.parametrize("method_name", ["increment", "decrement", "get"])
def test_plugin_method_calls_call_resolve(plugin_source, method_name):
    body = _extract_method_body(plugin_source["src"], method_name)
    assert body is not None, (
        f"CounterPlugin.java does not declare `{method_name}`; cannot check body."
    )
    assert re.search(r"\w+\s*\.\s*resolve\s*\(", body), (
        f"Method `{method_name}` in CounterPlugin.java must call call.resolve(...)."
    )


def test_main_activity_registers_counter_plugin():
    main_activity = os.path.join(ANDROID_APP_SRC, "MainActivity.java")
    assert os.path.isfile(main_activity), f"{main_activity} does not exist."
    with open(main_activity) as f:
        raw = f.read()
    stripped = _strip_comments(raw)

    m = re.search(
        r"void\s+onCreate\s*\(\s*Bundle\s+\w+\s*\)\s*\{", stripped
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
    pattern = r"registerPlugin\s*\(\s*CounterPlugin\s*\.\s*class\s*\)"
    assert re.search(pattern, body), (
        "MainActivity.onCreate must call registerPlugin(CounterPlugin.class)."
    )


def test_typescript_binding_exists_and_registers_plugin():
    binding = os.path.join(PROJECT_DIR, "src", "counter.ts")
    assert os.path.isfile(binding), f"{binding} does not exist."
    with open(binding) as f:
        ts = f.read()

    import_pattern = (
        r"import\s*\{[^}]*\bregisterPlugin\b[^}]*\}\s*from\s*['\"]@capacitor/core['\"]"
    )
    assert re.search(import_pattern, ts), (
        "src/counter.ts must import registerPlugin from '@capacitor/core'."
    )

    register_pattern = (
        r"registerPlugin\s*(?:<[^>]*>)?\s*\(\s*['\"]Counter['\"]"
    )
    assert re.search(register_pattern, ts), (
        "src/counter.ts must call registerPlugin with the exact string literal "
        '"Counter".'
    )

    assert re.search(r"export\s+default\s+", ts), (
        "src/counter.ts must have a default export."
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
        # Retry once without --offline in case of a transient cache miss.
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


def test_apk_dex_contains_counter_plugin_class():
    assert os.path.isfile(DEBUG_APK), (
        f"Debug APK {DEBUG_APK} not present; build step must run first."
    )
    descriptor = b"Lcom/example/myapp/CounterPlugin;"

    # Try classes.dex first, then classes2.dex, classes3.dex, ...
    members = ["classes.dex"] + [f"classes{i}.dex" for i in range(2, 10)]
    for member in members:
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
