import json
import os
import re

PROJECT_DIR = "/home/user/workspace/myapp"
PACKAGE_JSON = os.path.join(PROJECT_DIR, "package.json")
ANDROID_DIR = os.path.join(PROJECT_DIR, "android")
SYNCED_INDEX_HTML = os.path.join(
    ANDROID_DIR, "app", "src", "main", "assets", "public", "index.html"
)
DIST_INDEX_HTML = os.path.join(PROJECT_DIR, "dist", "index.html")


def _load_package_json() -> dict:
    assert os.path.isfile(PACKAGE_JSON), f"package.json not found at {PACKAGE_JSON}."
    with open(PACKAGE_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _find_first_existing(*candidates: str) -> str | None:
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _is_v8(version: str) -> bool:
    # Accept "8.x.y", "^8.x.y", "~8.x.y", "8" and similar v8-compatible spec strings.
    stripped = version.lstrip("^~>=< ")
    return stripped.startswith("8.") or stripped == "8" or stripped.startswith("8-")


def test_project_root_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected the Vite project to be scaffolded at {PROJECT_DIR}."
    )


def test_package_json_exists():
    assert os.path.isfile(PACKAGE_JSON), f"Missing package.json at {PACKAGE_JSON}."


def test_package_json_declares_react_runtime():
    pkg = _load_package_json()
    deps = pkg.get("dependencies", {}) or {}
    assert "react" in deps, (
        "package.json must declare 'react' as a runtime dependency."
    )
    assert "react-dom" in deps, (
        "package.json must declare 'react-dom' as a runtime dependency."
    )


def test_package_json_declares_vite_and_typescript_dev_deps():
    pkg = _load_package_json()
    dev = pkg.get("devDependencies", {}) or {}
    assert "typescript" in dev, (
        "package.json must declare 'typescript' under devDependencies "
        "(the Vite react-ts template includes it)."
    )
    assert "vite" in dev, (
        "package.json must declare 'vite' under devDependencies."
    )


def test_package_json_declares_capacitor_v8_runtime_packages():
    pkg = _load_package_json()
    deps = pkg.get("dependencies", {}) or {}
    assert "@capacitor/core" in deps, (
        "package.json must declare '@capacitor/core' under dependencies."
    )
    assert "@capacitor/android" in deps, (
        "package.json must declare '@capacitor/android' under dependencies."
    )
    assert _is_v8(deps["@capacitor/core"]), (
        "Expected @capacitor/core to be pinned to Capacitor v8.x, "
        f"got '{deps['@capacitor/core']}'."
    )
    assert _is_v8(deps["@capacitor/android"]), (
        "Expected @capacitor/android to be pinned to Capacitor v8.x, "
        f"got '{deps['@capacitor/android']}'."
    )


def test_package_json_declares_capacitor_cli_v8_dev_dep():
    pkg = _load_package_json()
    dev = pkg.get("devDependencies", {}) or {}
    assert "@capacitor/cli" in dev, (
        "package.json must declare '@capacitor/cli' under devDependencies."
    )
    assert _is_v8(dev["@capacitor/cli"]), (
        "Expected @capacitor/cli to be pinned to Capacitor v8.x, "
        f"got '{dev['@capacitor/cli']}'."
    )


def test_vite_config_sets_relative_base():
    vite_config = _find_first_existing(
        os.path.join(PROJECT_DIR, "vite.config.ts"),
        os.path.join(PROJECT_DIR, "vite.config.mts"),
        os.path.join(PROJECT_DIR, "vite.config.js"),
    )
    assert vite_config is not None, (
        "A vite.config.{ts,mts,js} file must exist at the project root."
    )
    with open(vite_config, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = re.compile(r"""base\s*:\s*['"]\./['"]""")
    assert pattern.search(content), (
        "vite.config must set the top-level Vite option `base: './'` so the WebView "
        "can resolve relative asset URLs. Got config:\n" + content
    )


def test_capacitor_config_has_required_fields():
    capacitor_config = _find_first_existing(
        os.path.join(PROJECT_DIR, "capacitor.config.ts"),
        os.path.join(PROJECT_DIR, "capacitor.config.js"),
        os.path.join(PROJECT_DIR, "capacitor.config.json"),
    )
    assert capacitor_config is not None, (
        "A capacitor.config.{ts,js,json} file must exist at the project root "
        "(produced by `npx cap init`)."
    )
    with open(capacitor_config, "r", encoding="utf-8") as f:
        content = f.read()

    if capacitor_config.endswith(".json"):
        data = json.loads(content)
        assert data.get("appId") == "com.example.myapp", (
            f"capacitor.config.json must set appId to 'com.example.myapp', got {data.get('appId')!r}."
        )
        assert data.get("appName") == "My App", (
            f"capacitor.config.json must set appName to 'My App', got {data.get('appName')!r}."
        )
        assert data.get("webDir") == "dist", (
            f"capacitor.config.json must set webDir to 'dist', got {data.get('webDir')!r}."
        )
    else:
        assert re.search(
            r"""appId\s*:\s*['"]com\.example\.myapp['"]""", content
        ), "capacitor.config must set appId to 'com.example.myapp'."
        assert re.search(r"""appName\s*:\s*['"]My App['"]""", content), (
            "capacitor.config must set appName to 'My App'."
        )
        assert re.search(r"""webDir\s*:\s*['"]dist['"]""", content), (
            "capacitor.config must set webDir to 'dist'."
        )


def test_android_platform_scaffolded():
    assert os.path.isdir(ANDROID_DIR), (
        f"Android platform directory {ANDROID_DIR} must exist (created by `npx cap add android`)."
    )
    required = [
        os.path.join(ANDROID_DIR, "build.gradle"),
        os.path.join(ANDROID_DIR, "settings.gradle"),
        os.path.join(ANDROID_DIR, "app", "build.gradle"),
        os.path.join(ANDROID_DIR, "gradlew"),
    ]
    for path in required:
        assert os.path.isfile(path), (
            f"Expected Android scaffold file {path} to exist."
        )


def test_synced_web_assets_present_in_android_project():
    assert os.path.isfile(SYNCED_INDEX_HTML), (
        f"`npx cap sync android` must have produced {SYNCED_INDEX_HTML}. "
        "Run `npm run build` before syncing."
    )
    with open(SYNCED_INDEX_HTML, "r", encoding="utf-8") as f:
        content = f.read()
    assert "./assets/" in content, (
        "The synced index.html must reference its bundles with relative URLs "
        "(strings containing './assets/'). Did you forget to set `base: './'` in vite.config?"
    )


def test_dist_index_html_uses_relative_asset_urls():
    assert os.path.isfile(DIST_INDEX_HTML), (
        f"Expected the Vite production build output at {DIST_INDEX_HTML}."
    )
    with open(DIST_INDEX_HTML, "r", encoding="utf-8") as f:
        content = f.read()
    # Absolute /assets/ references break the Android WebView when loading the
    # bundle from the local origin. The build must emit ./assets/... instead.
    assert not re.search(r"""src=["']/assets/""", content), (
        "dist/index.html must not contain absolute `src=\"/assets/...\"` references. "
        "Configure Vite with `base: './'` so it emits relative URLs."
    )
    assert not re.search(r"""href=["']/assets/""", content), (
        "dist/index.html must not contain absolute `href=\"/assets/...\"` references. "
        "Configure Vite with `base: './'` so it emits relative URLs."
    )
    assert "./assets/" in content, (
        "dist/index.html must reference its bundles via relative paths beginning with './assets/'."
    )
