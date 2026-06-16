import json
import os
import re
import xml.etree.ElementTree as ET

PROJECT_DIR = "/home/user/myproject"
CAPACITOR_CONFIG_JSON = os.path.join(PROJECT_DIR, "capacitor.config.json")
PKG_JSON = os.path.join(PROJECT_DIR, "package.json")
PLUGIN_PKG_JSON = os.path.join(
    PROJECT_DIR, "node_modules", "@capacitor", "splash-screen", "package.json"
)
STYLES_PATH = os.path.join(
    PROJECT_DIR, "android", "app", "src", "main", "res", "values", "styles.xml"
)
SPLASH_ICON_PATH = os.path.join(
    PROJECT_DIR,
    "android",
    "app",
    "src",
    "main",
    "res",
    "drawable",
    "splash_icon.xml",
)
SRC_DIR = os.path.join(PROJECT_DIR, "src")
WWW_DIR = os.path.join(PROJECT_DIR, "www")

ANDROID_NS = "http://schemas.android.com/apk/res/android"
SOURCE_EXTS = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")


def _load_package_json():
    with open(PKG_JSON) as f:
        return json.load(f)


def test_splash_screen_dependency_declared_in_package_json():
    data = _load_package_json()
    deps = data.get("dependencies") or {}
    assert "@capacitor/splash-screen" in deps, (
        "@capacitor/splash-screen must be declared under dependencies in "
        f"{PKG_JSON} (found dependencies: {sorted(deps.keys())})."
    )
    specifier = deps["@capacitor/splash-screen"]
    assert re.match(r"^[~^]?8(\.|$)", specifier), (
        "Expected @capacitor/splash-screen dependency specifier to resolve to the v8 "
        f"line (e.g. '^8.0.0'); got {specifier!r}."
    )


def test_splash_screen_plugin_installed_in_node_modules():
    assert os.path.isfile(PLUGIN_PKG_JSON), (
        f"@capacitor/splash-screen is not installed at {PLUGIN_PKG_JSON}. "
        "Run `npm install @capacitor/splash-screen@^8` inside the project."
    )
    with open(PLUGIN_PKG_JSON) as f:
        installed = json.load(f)
    version = installed.get("version", "")
    assert version.startswith("8."), (
        f"Installed @capacitor/splash-screen must be a v8 release; found {version!r}."
    )


def test_capacitor_config_plugin_section():
    assert os.path.isfile(CAPACITOR_CONFIG_JSON), (
        f"capacitor.config.json not found at {CAPACITOR_CONFIG_JSON}."
    )
    with open(CAPACITOR_CONFIG_JSON) as f:
        data = json.load(f)
    plugins = data.get("plugins")
    assert isinstance(plugins, dict), (
        "capacitor.config.json must contain a top-level 'plugins' object."
    )
    splash = plugins.get("SplashScreen")
    assert isinstance(splash, dict), (
        "capacitor.config.json must define plugins.SplashScreen as an object."
    )
    assert splash.get("launchAutoHide") is False, (
        f"plugins.SplashScreen.launchAutoHide must be the boolean false; "
        f"got {splash.get('launchAutoHide')!r}."
    )
    assert splash.get("launchShowDuration") == 2000, (
        f"plugins.SplashScreen.launchShowDuration must equal 2000; "
        f"got {splash.get('launchShowDuration')!r}."
    )
    assert splash.get("backgroundColor") == "#0E0E0E", (
        "plugins.SplashScreen.backgroundColor must be '#0E0E0E'; "
        f"got {splash.get('backgroundColor')!r}."
    )
    assert splash.get("androidScaleType") == "CENTER_CROP", (
        "plugins.SplashScreen.androidScaleType must be 'CENTER_CROP'; "
        f"got {splash.get('androidScaleType')!r}."
    )


def _find_launch_style(root):
    for style in root.findall("style"):
        if style.attrib.get("name") == "AppTheme.NoActionBarLaunch":
            return style
    return None


def test_android_styles_has_splash_attributes():
    assert os.path.isfile(STYLES_PATH), f"styles.xml not found at {STYLES_PATH}."
    tree = ET.parse(STYLES_PATH)
    root = tree.getroot()
    launch = _find_launch_style(root)
    assert launch is not None, (
        "styles.xml must contain a <style name=\"AppTheme.NoActionBarLaunch\"> element."
    )
    parent = launch.attrib.get("parent", "")
    assert parent == "Theme.SplashScreen", (
        "AppTheme.NoActionBarLaunch must use parent=\"Theme.SplashScreen\" so the "
        f"Android 12+ splash screen API is enabled; got parent={parent!r}."
    )

    items = {item.attrib.get("name"): (item.text or "").strip() for item in launch.findall("item")}
    assert "android:windowSplashScreenAnimatedIcon" in items, (
        "AppTheme.NoActionBarLaunch must declare "
        "<item name=\"android:windowSplashScreenAnimatedIcon\">."
    )
    assert items["android:windowSplashScreenAnimatedIcon"] == "@drawable/splash_icon", (
        "android:windowSplashScreenAnimatedIcon must reference '@drawable/splash_icon'; "
        f"got {items['android:windowSplashScreenAnimatedIcon']!r}."
    )
    assert "android:windowSplashScreenAnimationDuration" in items, (
        "AppTheme.NoActionBarLaunch must declare "
        "<item name=\"android:windowSplashScreenAnimationDuration\">."
    )
    assert items["android:windowSplashScreenAnimationDuration"] == "1000", (
        "android:windowSplashScreenAnimationDuration must equal '1000'; "
        f"got {items['android:windowSplashScreenAnimationDuration']!r}."
    )


def test_splash_icon_drawable_is_valid_vector():
    assert os.path.isfile(SPLASH_ICON_PATH), (
        f"Expected vector drawable at {SPLASH_ICON_PATH}."
    )
    tree = ET.parse(SPLASH_ICON_PATH)
    root = tree.getroot()
    # The tag includes the namespace in ElementTree's Clark notation only if the root
    # element uses a default xmlns. Capacitor/Android drawables typically declare the
    # `android` prefix, leaving the root unqualified.
    assert root.tag == "vector", (
        f"Root element of splash_icon.xml must be <vector>; got <{root.tag}>."
    )
    # Confirm the Android namespace is bound somewhere on the root element.
    namespaces = {v for v in root.attrib.values()}
    has_ns = ANDROID_NS in namespaces or any(
        ANDROID_NS in (v or "") for v in root.attrib.values()
    )
    # Fall back to parsing raw text to detect xmlns:android binding too.
    if not has_ns:
        with open(SPLASH_ICON_PATH) as f:
            has_ns = ANDROID_NS in f.read()
    assert has_ns, (
        f"splash_icon.xml must declare the Android namespace {ANDROID_NS} on its root "
        "element (typically as xmlns:android)."
    )
    # Look for at least one <path> descendant (qualified or unqualified).
    paths = [el for el in root.iter() if el.tag.split("}")[-1] == "path"]
    assert paths, (
        "splash_icon.xml must contain at least one <path> element inside the vector."
    )


def _collect_source_files():
    base = SRC_DIR if os.path.isdir(SRC_DIR) else WWW_DIR
    assert os.path.isdir(base), (
        f"Neither {SRC_DIR} nor {WWW_DIR} exists; cannot locate the web entry point."
    )
    matches = []
    for root, _dirs, files in os.walk(base):
        # Skip nested node_modules just in case
        if "node_modules" in root.split(os.sep):
            continue
        for name in files:
            if name.endswith(SOURCE_EXTS):
                matches.append(os.path.join(root, name))
    return matches


_IMPORT_RE = re.compile(
    r"""import\s*\{[^}]*\bSplashScreen\b[^}]*\}\s*from\s*['"]@capacitor/splash-screen['"]"""
)
_RAF_HIDE_RE = re.compile(
    r"requestAnimationFrame\s*\(\s*[^)]*?(?:=>|function[^{]*\{)[\s\S]*?SplashScreen\.hide\s*\(",
    re.MULTILINE,
)


def _strip_comments(text):
    # Remove /* ... */ and // ... comments to reduce false positives.
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    text = re.sub(r"(^|[^:])//[^\n]*", lambda m: m.group(1), text)
    return text


def test_javascript_hides_splash_after_first_frame():
    sources = _collect_source_files()
    assert sources, (
        "No JavaScript/TypeScript source files were found under the project's web "
        "directory; the executor must wire SplashScreen.hide() into the app."
    )

    matching_file = None
    raf_ok = False
    bad_top_level_call = False

    for path in sources:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
        clean = _strip_comments(raw)
        if not _IMPORT_RE.search(clean):
            continue
        matching_file = path
        if _RAF_HIDE_RE.search(clean):
            raf_ok = True
        # Detect top-level / non-wrapped hide() calls: occurrences of
        # SplashScreen.hide( that are not preceded by requestAnimationFrame in the
        # nearest surrounding code segment.
        for match in re.finditer(r"SplashScreen\.hide\s*\(", clean):
            start = match.start()
            preceding = clean[max(0, start - 400):start]
            if "requestAnimationFrame" not in preceding:
                bad_top_level_call = True
        break

    assert matching_file is not None, (
        "No source file imports `SplashScreen` from '@capacitor/splash-screen'."
    )
    assert raf_ok, (
        f"{matching_file} must call SplashScreen.hide() inside a requestAnimationFrame "
        "callback so the splash is dismissed only after the first frame is painted."
    )
    assert not bad_top_level_call, (
        f"{matching_file} contains a SplashScreen.hide() call that is not wrapped in "
        "requestAnimationFrame; the splash must only be hidden after the first frame "
        "is painted."
    )
