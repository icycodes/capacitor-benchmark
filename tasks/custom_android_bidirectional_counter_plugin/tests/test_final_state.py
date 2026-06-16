import os
import re
import subprocess

import pytest

PROJECT_DIR = "/home/user/myapp"
ANDROID_DIR = os.path.join(PROJECT_DIR, "android")
ANDROID_APP_SRC = os.path.join(
    ANDROID_DIR, "app", "src", "main", "java", "com", "example", "myapp"
)
PLUGIN_JAVA = os.path.join(ANDROID_APP_SRC, "CounterPlugin.java")
MAIN_ACTIVITY = os.path.join(ANDROID_APP_SRC, "MainActivity.java")
COUNTER_TS = os.path.join(PROJECT_DIR, "src", "counter.ts")
MAIN_TS = os.path.join(PROJECT_DIR, "src", "main.ts")
DEBUG_APK = os.path.join(
    ANDROID_DIR, "app", "build", "outputs", "apk", "debug", "app-debug.apk"
)


def _strip_comments(src: str) -> str:
    """Remove Java/TS-style line and block comments from source code."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    src = re.sub(r"//[^\n]*", "", src)
    return src


def _extract_block_body(stripped: str, signature_match: re.Match) -> str:
    """Given a regex match whose end() points to '{', return the matched block
    contents including the braces."""
    start = signature_match.end() - 1
    assert stripped[start] == "{", "Expected method body to start with '{'."
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
    assert end is not None, "Could not parse matching '}' for method body."
    return stripped[start : end + 1]


@pytest.fixture(scope="module")
def plugin_source():
    assert os.path.isfile(PLUGIN_JAVA), (
        f"Expected plugin source at {PLUGIN_JAVA} but it does not exist."
    )
    with open(PLUGIN_JAVA) as f:
        raw = f.read()
    stripped = _strip_comments(raw)
    return {"path": PLUGIN_JAVA, "raw": raw, "src": stripped}


def _extract_method_body(stripped: str, method_name: str) -> str:
    pattern = (
        r"@PluginMethod(?:\s*\([^)]*\))?\s+"
        rf"public\s+void\s+{re.escape(method_name)}\s*\("
        r"\s*PluginCall\s+\w+\s*\)\s*\{"
    )
    m = re.search(pattern, stripped)
    assert m, (
        f"Could not locate @PluginMethod-annotated `public void "
        f"{method_name}(PluginCall ...)` signature in plugin source."
    )
    return _extract_block_body(stripped, m)


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
        "CounterPlugin.java must be annotated with "
        '@CapacitorPlugin(name = "Counter").'
    )


def test_plugin_class_extends_plugin(plugin_source):
    assert re.search(
        r"public\s+class\s+CounterPlugin\s+extends\s+Plugin\b",
        plugin_source["src"],
    ), "CounterPlugin.java must declare `public class CounterPlugin extends Plugin`."


def test_plugin_has_int_instance_field(plugin_source):
    stripped = plugin_source["src"]
    # Find the class body and search only inside it.
    class_match = re.search(
        r"public\s+class\s+CounterPlugin\s+extends\s+Plugin\b[^{]*\{",
        stripped,
    )
    assert class_match, "Could not locate the CounterPlugin class declaration."
    body = _extract_block_body(stripped, class_match)
    # Look for an int field declaration at the class level (not inside a method).
    # Drop method bodies before searching to avoid matching local ints.
    body_no_methods = re.sub(
        r"(public|private|protected|static)?\s*"
        r"(final\s+)?"
        r"\w[\w<>,\s\[\]]*\s+\w+\s*\([^)]*\)\s*\{",
        "{",
        body,
    )
    field_pattern = (
        r"(?:public|private|protected|static|final|\s)+\s*int\s+\w+\s*"
        r"(?:=\s*[^;]+)?;"
    )
    # Fallback: search the raw class body for any "int <name>" field declaration.
    if not re.search(field_pattern, body_no_methods):
        # Strip method bodies (anything between '{' '}' inside the class) and retry.
        stripped_body = body
        # Remove nested braces (method bodies) iteratively.
        prev = None
        while prev != stripped_body:
            prev = stripped_body
            stripped_body = re.sub(r"\{[^{}]*\}", "{}", stripped_body)
        assert re.search(field_pattern, stripped_body), (
            "CounterPlugin.java must declare at least one `int` instance field "
            "to hold the counter value."
        )


def test_plugin_has_increment_reset_get_value_methods(plugin_source):
    stripped = plugin_source["src"]
    for name in ("increment", "reset", "getValue"):
        pattern = (
            r"@PluginMethod(?:\s*\([^)]*\))?\s+"
            rf"public\s+void\s+{re.escape(name)}\s*\("
            r"\s*PluginCall\s+\w+\s*\)"
        )
        assert re.search(pattern, stripped), (
            f"CounterPlugin.java does not declare a @PluginMethod-annotated "
            f"`public void {name}(PluginCall ...)` method."
        )


def test_increment_emits_change_event_and_resolves(plugin_source):
    body = _extract_method_body(plugin_source["src"], "increment")
    assert re.search(r'\bnotifyListeners\s*\(\s*"change"\s*,', body), (
        'increment() must call `notifyListeners("change", ...)` to emit the '
        "change event."
    )
    assert re.search(r'\.\s*put\s*\(\s*"value"\s*,', body), (
        'increment() must put the new counter value into a JSObject under the '
        '"value" key.'
    )
    assert re.search(r"\bcall\s*\.\s*resolve\s*\(", body), (
        "increment() must call `call.resolve(...)` to return the new value to JS."
    )


def test_reset_emits_change_event_and_resolves(plugin_source):
    body = _extract_method_body(plugin_source["src"], "reset")
    assert re.search(r'\bnotifyListeners\s*\(\s*"change"\s*,', body), (
        'reset() must call `notifyListeners("change", ...)` to emit the change '
        "event."
    )
    assert re.search(r'\.\s*put\s*\(\s*"value"\s*,', body), (
        'reset() must put the new counter value (0) into a JSObject under the '
        '"value" key.'
    )
    assert re.search(r"\bcall\s*\.\s*resolve\s*\(", body), (
        "reset() must call `call.resolve(...)` to return the reset value to JS."
    )


def test_get_value_resolves_but_does_not_emit(plugin_source):
    body = _extract_method_body(plugin_source["src"], "getValue")
    assert re.search(r"\bcall\s*\.\s*resolve\s*\(", body), (
        "getValue() must call `call.resolve(...)` to return the current value to JS."
    )
    assert not re.search(r"\bnotifyListeners\s*\(", body), (
        "getValue() must NOT call notifyListeners(); reading the value is not "
        "a state change."
    )


def test_main_activity_registers_counter_plugin():
    assert os.path.isfile(MAIN_ACTIVITY), f"{MAIN_ACTIVITY} does not exist."
    with open(MAIN_ACTIVITY) as f:
        raw = f.read()
    stripped = _strip_comments(raw)

    m = re.search(
        r"void\s+onCreate\s*\(\s*Bundle\s+\w+\s*\)\s*\{",
        stripped,
    )
    assert m, "MainActivity does not declare onCreate(Bundle ...)."
    body = _extract_block_body(stripped, m)
    assert re.search(
        r"registerPlugin\s*\(\s*CounterPlugin\s*\.\s*class\s*\)",
        body,
    ), "MainActivity.onCreate must call registerPlugin(CounterPlugin.class)."


def test_typescript_binding_registers_counter_plugin():
    assert os.path.isfile(COUNTER_TS), f"{COUNTER_TS} does not exist."
    with open(COUNTER_TS) as f:
        ts = f.read()
    stripped = _strip_comments(ts)

    import_pattern = (
        r"import\s*\{[^}]*\bregisterPlugin\b[^}]*\}\s*from\s*"
        r"['\"]@capacitor/core['\"]"
    )
    assert re.search(import_pattern, stripped), (
        "src/counter.ts must import registerPlugin from '@capacitor/core'."
    )

    register_pattern = (
        r"registerPlugin\s*(?:<[^>]*>)?\s*\(\s*['\"]Counter['\"]"
    )
    assert re.search(register_pattern, stripped), (
        "src/counter.ts must call registerPlugin with the exact string literal "
        '"Counter".'
    )

    assert re.search(r"export\s+default\s+", stripped), (
        "src/counter.ts must have a default export of the registered plugin."
    )


def test_typescript_binding_interface_declares_methods():
    with open(COUNTER_TS) as f:
        ts = f.read()
    stripped = _strip_comments(ts)
    # Find any interface or type alias declaration block.
    type_decls = re.findall(
        r"(?:interface\s+\w+\s*\{[^}]*\}|type\s+\w+\s*=\s*\{[^}]*\})",
        stripped,
        re.DOTALL,
    )
    assert type_decls, (
        "src/counter.ts must declare a TypeScript interface or type alias "
        "describing the Counter plugin."
    )
    for required in ("increment", "reset", "getValue", "addListener"):
        assert any(re.search(rf"\b{required}\b", decl) for decl in type_decls), (
            f"src/counter.ts plugin interface must declare a `{required}` member."
        )


def test_main_ts_uses_addListener_and_removes_via_handle():
    assert os.path.isfile(MAIN_TS), f"{MAIN_TS} does not exist."
    with open(MAIN_TS) as f:
        ts = f.read()
    stripped = _strip_comments(ts)

    import_pattern = r"import\s+(?:\w+|\*\s+as\s+\w+)\s+from\s+['\"]\./counter['\"]"
    assert re.search(import_pattern, stripped), (
        "src/main.ts must import the default export from './counter'."
    )

    add_listener_pattern = (
        r"\.addListener\s*\(\s*['\"]change['\"]\s*,"
    )
    assert re.search(add_listener_pattern, stripped), (
        "src/main.ts must call `addListener('change', ...)` on the Counter "
        "plugin."
    )

    # The handle returned by addListener must be stored in a variable. Allow:
    #   const handle = Counter.addListener(...)
    #   const handle = await Counter.addListener(...)
    #   let handle: ... = Counter.addListener(...)
    handle_assignment = re.search(
        r"(?:const|let|var)\s+(\w+)(?:\s*:\s*[^=;]+)?\s*=\s*"
        r"(?:await\s+)?[\w\.]*addListener\s*\(\s*['\"]change['\"]\s*,",
        stripped,
    )
    assert handle_assignment, (
        "src/main.ts must store the listener handle returned by "
        "`addListener('change', ...)` in a variable."
    )
    handle_name = handle_assignment.group(1)

    # Then it must call .remove() on that handle. Allow `handle.remove()` or
    # `(await handle).remove()`.
    remove_pattern = (
        rf"(?:\bawait\s+)?{re.escape(handle_name)}\s*\.\s*remove\s*\("
        rf"|\(\s*await\s+{re.escape(handle_name)}\s*\)\s*\.\s*remove\s*\("
    )
    assert re.search(remove_pattern, stripped), (
        f"src/main.ts must call `.remove()` on the stored listener handle "
        f"variable `{handle_name}` to detach the listener."
    )


def test_typescript_sources_typecheck():
    tsconfig = os.path.join(PROJECT_DIR, "tsconfig.json")
    assert os.path.isfile(tsconfig), f"tsconfig.json not found at {tsconfig}."
    result = subprocess.run(
        ["npx", "--offline", "tsc", "--noEmit", "-p", "tsconfig.json"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        # Retry once without --offline to recover from any transient cache miss.
        result = subprocess.run(
            ["npx", "tsc", "--noEmit", "-p", "tsconfig.json"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=600,
        )
    assert result.returncode == 0, (
        f"TypeScript type-check failed (exit={result.returncode}).\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
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
