import os
import re
import subprocess

PROJECT_DIR = "/home/user/myapp"
IOS_DIR = os.path.join(PROJECT_DIR, "ios")
IOS_APP_DIR = os.path.join(IOS_DIR, "App", "App")
ECHO_PLUGIN_PATH = os.path.join(IOS_APP_DIR, "EchoPlugin.swift")
MY_VC_PATH = os.path.join(IOS_APP_DIR, "MyViewController.swift")
PBXPROJ_PATH = os.path.join(IOS_DIR, "App", "App.xcodeproj", "project.pbxproj")
ECHO_TS_PATH = os.path.join(PROJECT_DIR, "src", "echo.ts")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_echo_plugin_swift_exists():
    assert os.path.isfile(ECHO_PLUGIN_PATH), (
        f"Expected Swift plugin source at {ECHO_PLUGIN_PATH} but it does not exist."
    )


def test_echo_plugin_swift_imports_capacitor():
    content = _read(ECHO_PLUGIN_PATH)
    assert re.search(r"^\s*import\s+Capacitor\b", content, re.MULTILINE), (
        "EchoPlugin.swift must contain `import Capacitor` at the top of the file."
    )


def test_echo_plugin_swift_objc_annotation():
    content = _read(ECHO_PLUGIN_PATH)
    assert re.search(r"@objc\s*\(\s*EchoPlugin\s*\)", content), (
        "EchoPlugin.swift must declare `@objc(EchoPlugin)` to expose the class to the Objective-C runtime."
    )


def test_echo_plugin_swift_class_declaration():
    content = _read(ECHO_PLUGIN_PATH)
    # Order-tolerant: either CAPPlugin, CAPBridgedPlugin or the reverse.
    pattern = (
        r"class\s+EchoPlugin\s*:\s*"
        r"(CAPPlugin\s*,\s*CAPBridgedPlugin|CAPBridgedPlugin\s*,\s*CAPPlugin)"
    )
    assert re.search(pattern, content), (
        "EchoPlugin must be declared as `class EchoPlugin: CAPPlugin, CAPBridgedPlugin` "
        "(order of the conformances may vary)."
    )


def test_echo_plugin_swift_identifier_constant():
    content = _read(ECHO_PLUGIN_PATH)
    assert re.search(
        r'public\s+let\s+identifier\s*=\s*"EchoPlugin"',
        content,
    ), 'EchoPlugin.swift must declare `public let identifier = "EchoPlugin"`.'


def test_echo_plugin_swift_jsname_constant():
    content = _read(ECHO_PLUGIN_PATH)
    assert re.search(
        r'public\s+let\s+jsName\s*=\s*"Echo"',
        content,
    ), 'EchoPlugin.swift must declare `public let jsName = "Echo"`.'


def test_echo_plugin_swift_plugin_methods_array():
    content = _read(ECHO_PLUGIN_PATH)
    assert re.search(
        r"pluginMethods\s*:\s*\[\s*CAPPluginMethod\s*\]",
        content,
    ), 'EchoPlugin.swift must declare a `pluginMethods: [CAPPluginMethod]` array literal.'
    assert re.search(
        r'CAPPluginMethod\s*\(\s*name\s*:\s*"echo"\s*,\s*returnType\s*:\s*CAPPluginReturnPromise\s*\)',
        content,
    ), (
        "EchoPlugin.swift must include `CAPPluginMethod(name: \"echo\", returnType: CAPPluginReturnPromise)` "
        "inside its pluginMethods array."
    )


def test_echo_plugin_swift_echo_method_signature():
    content = _read(ECHO_PLUGIN_PATH)
    assert re.search(
        r"@objc\s+func\s+echo\s*\(\s*_\s+call\s*:\s*CAPPluginCall\s*\)",
        content,
    ), (
        "EchoPlugin.swift must define `@objc func echo(_ call: CAPPluginCall)`."
    )


def test_echo_plugin_swift_resolves_value_key():
    content = _read(ECHO_PLUGIN_PATH)
    # Match a call.resolve(...) whose argument dictionary contains a "value" key.
    pattern = r"call\.resolve\s*\(\s*\[[^\]]*\"value\"\s*:\s*[^\]]*\]\s*\)"
    assert re.search(pattern, content), (
        "EchoPlugin.swift must call `call.resolve([... \"value\": ... ])` "
        "to return the echoed value back to JavaScript."
    )


def test_echo_plugin_swift_balanced_braces():
    content = _read(ECHO_PLUGIN_PATH)
    opens = content.count("{")
    closes = content.count("}")
    assert opens == closes, (
        f"EchoPlugin.swift has unbalanced curly braces: {opens} '{{' vs {closes} '}}'."
    )
    assert opens >= 4, (
        f"EchoPlugin.swift should contain at least 4 opening braces (class, "
        f"pluginMethods, method body, etc.); found {opens}."
    )


def test_myviewcontroller_registers_echo_plugin():
    content = _read(MY_VC_PATH)
    assert re.search(
        r"override\s+open\s+func\s+capacitorDidLoad\s*\(\s*\)",
        content,
    ) or re.search(
        r"override\s+public\s+func\s+capacitorDidLoad\s*\(\s*\)",
        content,
    ) or re.search(
        r"override\s+func\s+capacitorDidLoad\s*\(\s*\)",
        content,
    ), (
        "MyViewController.swift must override `capacitorDidLoad()`."
    )
    assert re.search(
        r"bridge\s*\?\s*\.\s*registerPluginInstance\s*\(\s*EchoPlugin\s*\(\s*\)\s*\)",
        content,
    ), (
        "MyViewController.swift must call `bridge?.registerPluginInstance(EchoPlugin())` "
        "inside `capacitorDidLoad()`."
    )


def test_pbxproj_references_echo_plugin_swift():
    content = _read(PBXPROJ_PATH)
    occurrences = content.count("EchoPlugin.swift")
    assert occurrences >= 2, (
        f"project.pbxproj must reference `EchoPlugin.swift` at least twice "
        f"(once in PBXFileReference and once in PBXSourcesBuildPhase); "
        f"found {occurrences} occurrence(s)."
    )


def test_echo_ts_wrapper_exists_and_registers_plugin():
    assert os.path.isfile(ECHO_TS_PATH), (
        f"TypeScript wrapper {ECHO_TS_PATH} must exist."
    )
    content = _read(ECHO_TS_PATH)
    assert re.search(
        r"import\s*\{[^}]*\bregisterPlugin\b[^}]*\}\s*from\s*['\"]@capacitor/core['\"]",
        content,
    ), (
        "src/echo.ts must import `registerPlugin` from `@capacitor/core`."
    )
    assert re.search(
        r"registerPlugin\s*(?:<[^>]+>)?\s*\(\s*['\"]Echo['\"]",
        content,
    ), (
        "src/echo.ts must call `registerPlugin('Echo')` (or `registerPlugin<...>('Echo')`)."
    )


def test_cap_sync_ios_succeeds():
    result = subprocess.run(
        ["npx", "--no-install", "cap", "sync", "ios"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, (
        f"`npx cap sync ios` failed with exit code {result.returncode}.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
