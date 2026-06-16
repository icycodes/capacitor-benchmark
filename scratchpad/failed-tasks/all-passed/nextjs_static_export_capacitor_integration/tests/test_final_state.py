import filecmp
import json
import os
import re
import shutil
import subprocess

import pytest

PROJECT_DIR = "/home/user/myapp"
ANDROID_DIR = os.path.join(PROJECT_DIR, "android")
OUT_DIR = os.path.join(PROJECT_DIR, "out")
ANDROID_ASSETS_PUBLIC = os.path.join(
    ANDROID_DIR, "app", "src", "main", "assets", "public"
)
LIB_HASH_ROUTER = os.path.join(PROJECT_DIR, "lib", "hashRouter.ts")


def _strip_ts_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    src = re.sub(r"//[^\n]*", "", src)
    return src


def _find_next_config() -> str:
    for fname in ("next.config.js", "next.config.mjs"):
        path = os.path.join(PROJECT_DIR, fname)
        if os.path.isfile(path):
            return path
    raise AssertionError(
        f"Expected a next.config.js or next.config.mjs in {PROJECT_DIR}."
    )


def _find_capacitor_config() -> str:
    for fname in ("capacitor.config.ts", "capacitor.config.json"):
        path = os.path.join(PROJECT_DIR, fname)
        if os.path.isfile(path):
            return path
    raise AssertionError(
        f"Expected a capacitor.config.ts or capacitor.config.json in {PROJECT_DIR}."
    )


@pytest.fixture(scope="module")
def loaded_next_config() -> dict:
    """Evaluate the next.config file (CJS or ESM) and return the exported config object."""
    path = _find_next_config()
    # Use a small Node loader that supports both CJS and ESM (Next 14 supports both).
    if path.endswith(".mjs"):
        loader = (
            "(async () => { const m = await import(process.argv[1]); "
            "process.stdout.write(JSON.stringify(m.default || m)); })()"
        )
    else:
        loader = (
            "(async () => { let cfg; try { cfg = require(process.argv[1]); } "
            "catch (e) { const m = await import(process.argv[1]); cfg = m.default || m; } "
            "if (typeof cfg === 'function') cfg = await cfg(); "
            "process.stdout.write(JSON.stringify(cfg)); })()"
        )
    result = subprocess.run(
        ["node", "-e", loader, path],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"Failed to load Next.js config at {path}: "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    try:
        return json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"Could not parse Next.js config output as JSON: {result.stdout!r} ({exc})"
        )


def test_next_config_has_output_export(loaded_next_config):
    assert loaded_next_config.get("output") == "export", (
        "next.config must declare output: 'export' for static export, got "
        f"{loaded_next_config.get('output')!r}."
    )


def test_next_config_has_trailing_slash_true(loaded_next_config):
    assert loaded_next_config.get("trailingSlash") is True, (
        "next.config must declare trailingSlash: true for native WebView routing, "
        f"got {loaded_next_config.get('trailingSlash')!r}."
    )


def test_next_config_images_unoptimized_true(loaded_next_config):
    images = loaded_next_config.get("images")
    assert isinstance(images, dict), (
        f"next.config.images must be an object, got {images!r}."
    )
    assert images.get("unoptimized") is True, (
        "next.config.images.unoptimized must be true for static export, got "
        f"{images.get('unoptimized')!r}."
    )


def test_package_json_declares_capacitor_v8_packages():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg_path) as f:
        pkg = json.load(f)
    deps = pkg.get("dependencies", {})
    dev_deps = pkg.get("devDependencies", {})

    assert "@capacitor/core" in deps, (
        "@capacitor/core must be declared in dependencies of package.json."
    )
    assert "@capacitor/android" in deps, (
        "@capacitor/android must be declared in dependencies of package.json."
    )
    assert "@capacitor/cli" in dev_deps, (
        "@capacitor/cli must be declared in devDependencies of package.json."
    )

    # Each declared version range must mention an 8.x line.
    for section, name, value in (
        ("dependencies", "@capacitor/core", deps.get("@capacitor/core", "")),
        ("dependencies", "@capacitor/android", deps.get("@capacitor/android", "")),
        ("devDependencies", "@capacitor/cli", dev_deps.get("@capacitor/cli", "")),
    ):
        assert re.search(r"(^|[^\d])8\.", value) or value.startswith("^8") or value.startswith("~8") or value.startswith("8"), (
            f"{section}[{name}] must resolve to Capacitor v8 (got {value!r})."
        )


@pytest.mark.parametrize(
    "subpkg", ["core", "android", "cli"]
)
def test_capacitor_modules_installed_at_v8(subpkg):
    pkg_path = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", subpkg, "package.json"
    )
    assert os.path.isfile(pkg_path), (
        f"@capacitor/{subpkg} is not installed under node_modules at {pkg_path}."
    )
    with open(pkg_path) as f:
        pkg = json.load(f)
    version = pkg.get("version", "")
    assert version.startswith("8."), (
        f"Installed @capacitor/{subpkg} must be v8 (got {version!r})."
    )


def test_capacitor_config_has_correct_app_metadata_and_web_dir():
    path = _find_capacitor_config()
    with open(path) as f:
        raw = f.read()

    if path.endswith(".json"):
        cfg = json.loads(raw)
        assert cfg.get("appId") == "com.example.myapp", (
            f"capacitor.config.json appId must be 'com.example.myapp' (got "
            f"{cfg.get('appId')!r})."
        )
        assert cfg.get("appName") == "MyApp", (
            f"capacitor.config.json appName must be 'MyApp' (got "
            f"{cfg.get('appName')!r})."
        )
        assert cfg.get("webDir") == "out", (
            f"capacitor.config.json webDir must be 'out' (got "
            f"{cfg.get('webDir')!r})."
        )
    else:
        stripped = _strip_ts_comments(raw)
        assert re.search(
            r"appId\s*:\s*['\"]com\.example\.myapp['\"]", stripped
        ), (
            "capacitor.config.ts must declare appId: 'com.example.myapp'."
        )
        assert re.search(r"appName\s*:\s*['\"]MyApp['\"]", stripped), (
            "capacitor.config.ts must declare appName: 'MyApp'."
        )
        assert re.search(r"webDir\s*:\s*['\"]out['\"]", stripped), (
            "capacitor.config.ts must declare webDir: 'out'."
        )


def test_hash_router_helper_exists_and_exports_navigate_and_current_path():
    assert os.path.isfile(LIB_HASH_ROUTER), (
        f"Expected hash routing helper at {LIB_HASH_ROUTER}."
    )
    with open(LIB_HASH_ROUTER) as f:
        raw = f.read()
    stripped = _strip_ts_comments(raw)

    # navigate(path: string) writes to window.location.hash
    assert re.search(
        r"export\s+function\s+navigate\s*\(", stripped
    ) or re.search(
        r"export\s+const\s+navigate\s*=\s*\(", stripped
    ) or re.search(
        r"export\s*\{[^}]*\bnavigate\b[^}]*\}", stripped
    ), (
        "lib/hashRouter.ts must export a function named `navigate`."
    )
    assert re.search(r"window\s*\.\s*location\s*\.\s*hash\s*=", stripped), (
        "lib/hashRouter.ts `navigate` implementation must assign to "
        "`window.location.hash`."
    )

    # currentPath(): string reads window.location.hash
    assert re.search(
        r"export\s+function\s+currentPath\s*\(", stripped
    ) or re.search(
        r"export\s+const\s+currentPath\s*=\s*\(", stripped
    ) or re.search(
        r"export\s*\{[^}]*\bcurrentPath\b[^}]*\}", stripped
    ), (
        "lib/hashRouter.ts must export a function named `currentPath`."
    )
    assert re.search(r"window\s*\.\s*location\s*\.\s*hash\b", stripped), (
        "lib/hashRouter.ts `currentPath` implementation must read "
        "`window.location.hash`."
    )


def test_android_platform_scaffolded():
    assert os.path.isdir(ANDROID_DIR), (
        f"Android project directory {ANDROID_DIR} does not exist."
    )
    assert os.path.isfile(os.path.join(ANDROID_DIR, "build.gradle")), (
        "android/build.gradle is missing — cap add android may not have run."
    )
    manifest = os.path.join(
        ANDROID_DIR, "app", "src", "main", "AndroidManifest.xml"
    )
    assert os.path.isfile(manifest), (
        f"AndroidManifest.xml is missing at {manifest}."
    )


def test_next_build_produces_static_export_directory():
    # Clean any prior export so we exercise a real build.
    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)

    env = os.environ.copy()
    env.setdefault("CI", "1")
    env.setdefault("NEXT_TELEMETRY_DISABLED", "1")

    result = subprocess.run(
        ["npx", "--no-install", "next", "build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        env=env,
        timeout=600,
    )
    assert result.returncode == 0, (
        f"'next build' failed (exit={result.returncode}).\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    assert os.path.isdir(OUT_DIR), (
        f"'next build' did not produce the static export directory at {OUT_DIR}."
    )
    assert os.path.isfile(os.path.join(OUT_DIR, "index.html")), (
        f"Expected {OUT_DIR}/index.html to be produced by `next build`."
    )


def test_cap_sync_android_copies_out_into_native_assets():
    # Ensure native assets dir is cleaned so this test verifies a real sync.
    if os.path.isdir(ANDROID_ASSETS_PUBLIC):
        shutil.rmtree(ANDROID_ASSETS_PUBLIC)

    env = os.environ.copy()
    env.setdefault("CI", "1")

    result = subprocess.run(
        ["npx", "--no-install", "cap", "sync", "android"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        env=env,
        timeout=600,
    )
    assert result.returncode == 0, (
        f"'npx cap sync android' failed (exit={result.returncode}).\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )

    synced_index = os.path.join(ANDROID_ASSETS_PUBLIC, "index.html")
    assert os.path.isfile(synced_index), (
        f"cap sync did not copy index.html to {synced_index}."
    )

    out_index = os.path.join(OUT_DIR, "index.html")
    assert os.path.isfile(out_index), (
        f"Static export {out_index} is missing; cannot compare with synced asset."
    )
    assert filecmp.cmp(synced_index, out_index, shallow=False), (
        f"Synced {synced_index} does not match the static export "
        f"{out_index}; cap sync did not copy the latest build output."
    )
