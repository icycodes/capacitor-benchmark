import os
import re
import subprocess

PROJECT_DIR = "/home/user/myapp"
IOS_DIR = os.path.join(PROJECT_DIR, "ios")
IOS_APP_DIR = os.path.join(IOS_DIR, "App", "App")
TIMER_PLUGIN_PATH = os.path.join(IOS_APP_DIR, "TimerEmitterPlugin.swift")
MY_VC_PATH = os.path.join(IOS_APP_DIR, "MyViewController.swift")
PBXPROJ_PATH = os.path.join(IOS_DIR, "App", "App.xcodeproj", "project.pbxproj")
TIMER_TS_PATH = os.path.join(PROJECT_DIR, "src", "timer-emitter.ts")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_timer_emitter_plugin_swift_exists():
    assert os.path.isfile(TIMER_PLUGIN_PATH), (
        f"Expected Swift plugin source at {TIMER_PLUGIN_PATH} but it does not exist."
    )


def test_timer_emitter_plugin_swift_imports_capacitor():
    content = _read(TIMER_PLUGIN_PATH)
    assert re.search(r"^\s*import\s+Capacitor\b", content, re.MULTILINE), (
        "TimerEmitterPlugin.swift must contain `import Capacitor` at the top of the file."
    )


def test_timer_emitter_plugin_swift_objc_annotation():
    content = _read(TIMER_PLUGIN_PATH)
    assert re.search(r"@objc\s*\(\s*TimerEmitterPlugin\s*\)", content), (
        "TimerEmitterPlugin.swift must declare `@objc(TimerEmitterPlugin)` to expose the class "
        "to the Objective-C runtime."
    )


def test_timer_emitter_plugin_swift_class_declaration():
    content = _read(TIMER_PLUGIN_PATH)
    # Order-tolerant: either CAPPlugin, CAPBridgedPlugin or the reverse.
    pattern = (
        r"class\s+TimerEmitterPlugin\s*:\s*"
        r"(CAPPlugin\s*,\s*CAPBridgedPlugin|CAPBridgedPlugin\s*,\s*CAPPlugin)"
    )
    assert re.search(pattern, content), (
        "TimerEmitterPlugin must be declared as "
        "`class TimerEmitterPlugin: CAPPlugin, CAPBridgedPlugin` "
        "(order of the conformances may vary)."
    )


def test_timer_emitter_plugin_swift_identifier_constant():
    content = _read(TIMER_PLUGIN_PATH)
    assert re.search(
        r'public\s+let\s+identifier\s*=\s*"TimerEmitterPlugin"',
        content,
    ), 'TimerEmitterPlugin.swift must declare `public let identifier = "TimerEmitterPlugin"`.'


def test_timer_emitter_plugin_swift_jsname_constant():
    content = _read(TIMER_PLUGIN_PATH)
    assert re.search(
        r'public\s+let\s+jsName\s*=\s*"TimerEmitter"',
        content,
    ), 'TimerEmitterPlugin.swift must declare `public let jsName = "TimerEmitter"`.'


def test_timer_emitter_plugin_swift_plugin_methods_array():
    content = _read(TIMER_PLUGIN_PATH)
    assert re.search(
        r"pluginMethods\s*:\s*\[\s*CAPPluginMethod\s*\]",
        content,
    ), 'TimerEmitterPlugin.swift must declare a `pluginMethods: [CAPPluginMethod]` array literal.'
    assert re.search(
        r'CAPPluginMethod\s*\(\s*name\s*:\s*"startTimer"\s*,\s*returnType\s*:\s*CAPPluginReturnPromise\s*\)',
        content,
    ), (
        "TimerEmitterPlugin.swift must include "
        "`CAPPluginMethod(name: \"startTimer\", returnType: CAPPluginReturnPromise)` "
        "inside its pluginMethods array."
    )
    assert re.search(
        r'CAPPluginMethod\s*\(\s*name\s*:\s*"stopTimer"\s*,\s*returnType\s*:\s*CAPPluginReturnPromise\s*\)',
        content,
    ), (
        "TimerEmitterPlugin.swift must include "
        "`CAPPluginMethod(name: \"stopTimer\", returnType: CAPPluginReturnPromise)` "
        "inside its pluginMethods array."
    )


def test_timer_emitter_plugin_swift_start_timer_method_signature():
    content = _read(TIMER_PLUGIN_PATH)
    assert re.search(
        r"@objc\s+func\s+startTimer\s*\(\s*_\s+call\s*:\s*CAPPluginCall\s*\)",
        content,
    ), (
        "TimerEmitterPlugin.swift must define "
        "`@objc func startTimer(_ call: CAPPluginCall)`."
    )


def test_timer_emitter_plugin_swift_stop_timer_method_signature():
    content = _read(TIMER_PLUGIN_PATH)
    assert re.search(
        r"@objc\s+func\s+stopTimer\s*\(\s*_\s+call\s*:\s*CAPPluginCall\s*\)",
        content,
    ), (
        "TimerEmitterPlugin.swift must define "
        "`@objc func stopTimer(_ call: CAPPluginCall)`."
    )


def test_timer_emitter_plugin_swift_uses_scheduled_timer():
    content = _read(TIMER_PLUGIN_PATH)
    assert re.search(r"Timer\.scheduledTimer\s*\(", content), (
        "TimerEmitterPlugin.swift must call `Timer.scheduledTimer(...)` to start the "
        "repeating timer."
    )


def test_timer_emitter_plugin_swift_notifies_tick_with_count():
    content = _read(TIMER_PLUGIN_PATH)
    # notifyListeners("tick", data: [ ... "count": ... ])
    pattern = (
        r'notifyListeners\s*\(\s*"tick"\s*,\s*data\s*:\s*\[[^\]]*"count"\s*:'
    )
    assert re.search(pattern, content, re.DOTALL), (
        'TimerEmitterPlugin.swift must call '
        '`notifyListeners("tick", data: ["count": ...])` to push events to JavaScript.'
    )


def test_timer_emitter_plugin_swift_invalidates_timer():
    content = _read(TIMER_PLUGIN_PATH)
    assert re.search(r"\.invalidate\s*\(\s*\)", content), (
        "TimerEmitterPlugin.swift must call `.invalidate()` on the timer (in stopTimer "
        "and/or before restarting)."
    )


def test_timer_emitter_plugin_swift_balanced_braces():
    content = _read(TIMER_PLUGIN_PATH)
    opens = content.count("{")
    closes = content.count("}")
    assert opens == closes, (
        f"TimerEmitterPlugin.swift has unbalanced curly braces: {opens} '{{' vs {closes} '}}'."
    )
    assert opens >= 6, (
        f"TimerEmitterPlugin.swift should contain at least 6 opening braces (class, "
        f"pluginMethods, two method bodies, timer closure, etc.); found {opens}."
    )


def test_myviewcontroller_registers_timer_emitter_plugin():
    content = _read(MY_VC_PATH)
    assert (
        re.search(
            r"override\s+open\s+func\s+capacitorDidLoad\s*\(\s*\)",
            content,
        )
        or re.search(
            r"override\s+public\s+func\s+capacitorDidLoad\s*\(\s*\)",
            content,
        )
        or re.search(
            r"override\s+func\s+capacitorDidLoad\s*\(\s*\)",
            content,
        )
    ), "MyViewController.swift must override `capacitorDidLoad()`."
    assert re.search(
        r"bridge\s*\?\s*\.\s*registerPluginInstance\s*\(\s*TimerEmitterPlugin\s*\(\s*\)\s*\)",
        content,
    ), (
        "MyViewController.swift must call "
        "`bridge?.registerPluginInstance(TimerEmitterPlugin())` "
        "inside `capacitorDidLoad()`."
    )


def test_pbxproj_references_timer_emitter_plugin_swift():
    content = _read(PBXPROJ_PATH)
    occurrences = content.count("TimerEmitterPlugin.swift")
    assert occurrences >= 2, (
        f"project.pbxproj must reference `TimerEmitterPlugin.swift` at least twice "
        f"(once in PBXFileReference and once in PBXSourcesBuildPhase); "
        f"found {occurrences} occurrence(s)."
    )


def test_timer_emitter_ts_wrapper_exists_and_registers_plugin():
    assert os.path.isfile(TIMER_TS_PATH), (
        f"TypeScript wrapper {TIMER_TS_PATH} must exist."
    )
    content = _read(TIMER_TS_PATH)
    assert re.search(
        r"import\s*\{[^}]*\bregisterPlugin\b[^}]*\}\s*from\s*['\"]@capacitor/core['\"]",
        content,
    ), "src/timer-emitter.ts must import `registerPlugin` from `@capacitor/core`."
    assert re.search(
        r"registerPlugin\s*(?:<[^>]+>)?\s*\(\s*['\"]TimerEmitter['\"]",
        content,
    ), (
        "src/timer-emitter.ts must call `registerPlugin('TimerEmitter')` "
        "(or `registerPlugin<...>('TimerEmitter')`)."
    )
    # Interface should describe startTimer with intervalMs parameter.
    assert re.search(
        r"startTimer\s*\(\s*[A-Za-z0-9_]*\s*:?\s*\{[^}]*intervalMs\s*:\s*number",
        content,
        re.DOTALL,
    ), (
        "src/timer-emitter.ts must declare a `startTimer` method whose options object "
        "includes an `intervalMs: number` field."
    )
    # Should declare stopTimer method.
    assert re.search(r"stopTimer\s*\(\s*\)", content), (
        "src/timer-emitter.ts must declare a `stopTimer()` method on the plugin interface."
    )
    # Should declare an addListener overload for the 'tick' event with a {count: number} payload.
    assert re.search(
        r"addListener\s*\(\s*['\"]tick['\"]",
        content,
    ), (
        "src/timer-emitter.ts must declare an `addListener('tick', ...)` overload "
        "on the plugin interface."
    )
    assert re.search(
        r"count\s*:\s*number",
        content,
    ), (
        "src/timer-emitter.ts must type the `tick` event payload with a "
        "`count: number` field."
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
