import json
import os
import re
import shutil
import subprocess

import pytest

PROJECT_DIR = "/home/user/myapp"

REQUIRED_OPTIONS = {
    "launchShowDuration": 3000,
    "backgroundColor": "#ffffffff",
    "showSpinner": True,
    "androidSpinnerStyle": "large",
    "iosSpinnerStyle": "small",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_package_json():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), f"package.json not found at {pkg_path}."
    with open(pkg_path) as f:
        return json.load(f), pkg_path


def _find_capacitor_config():
    """Return (path, fmt) for the Capacitor config file, preferring .ts/.js over .json."""
    candidates = [
        ("capacitor.config.ts", "ts"),
        ("capacitor.config.js", "js"),
        ("capacitor.config.json", "json"),
    ]
    for name, fmt in candidates:
        path = os.path.join(PROJECT_DIR, name)
        if os.path.isfile(path):
            return path, fmt
    raise AssertionError(
        "Expected a Capacitor config file (capacitor.config.ts/js/json) at the "
        f"project root {PROJECT_DIR}."
    )


def _evaluate_splashscreen_via_tsx():
    """Use `npx tsx` to evaluate the Capacitor config and dump plugins.SplashScreen."""
    config_path, fmt = _find_capacitor_config()

    if fmt == "json":
        with open(config_path) as f:
            cfg = json.load(f)
        plugins = cfg.get("plugins") if isinstance(cfg, dict) else None
        if not isinstance(plugins, dict):
            return None
        sp = plugins.get("SplashScreen")
        return sp if isinstance(sp, dict) else None

    # TS / JS: evaluate with tsx so any TypeScript syntax (CapacitorConfig type
    # annotations etc.) does not trip the verifier.
    if shutil.which("npx") is None:
        return None

    script = (
        "import config from '" + config_path + "';"
        "const plugins = (config && (config.default ?? config).plugins) || {};"
        "const sp = plugins.SplashScreen ?? null;"
        "process.stdout.write(JSON.stringify(sp));"
    )

    result = subprocess.run(
        ["npx", "--yes", "tsx", "-e", script],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        return None
    out = result.stdout.strip()
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def _regex_check_splashscreen(config_path):
    """Fallback: regex search the TS/JS source for each required option literal."""
    with open(config_path) as f:
        content = f.read()
    # Locate the SplashScreen: { ... } block; use a generous DOTALL match.
    block_match = re.search(
        r"SplashScreen\s*:\s*\{(?P<body>.*?)\}", content, re.DOTALL
    )
    assert block_match, (
        f"Could not find a `SplashScreen: {{ ... }}` block in {config_path}."
    )
    body = block_match.group("body")

    patterns = {
        "launchShowDuration": r"launchShowDuration\s*:\s*3000\b",
        "backgroundColor": r"""backgroundColor\s*:\s*['"]#ffffffff['"]""",
        "showSpinner": r"showSpinner\s*:\s*true\b",
        "androidSpinnerStyle": r"""androidSpinnerStyle\s*:\s*['"]large['"]""",
        "iosSpinnerStyle": r"""iosSpinnerStyle\s*:\s*['"]small['"]""",
    }
    for key, pattern in patterns.items():
        assert re.search(pattern, body), (
            f"Regex fallback: capacitor config at {config_path} must set "
            f"plugins.SplashScreen.{key} to the required value."
        )


# ---------------------------------------------------------------------------
# Build / sync verification (must run first so dist/ exists for any later step)
# ---------------------------------------------------------------------------


def test_npm_build_succeeds_and_produces_dist_index_html():
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Expected `npm run build` to exit 0.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    dist_index = os.path.join(PROJECT_DIR, "dist", "index.html")
    assert os.path.isfile(dist_index), (
        f"Expected production build output at {dist_index} after `npm run build`."
    )


def test_capacitor_sync_succeeds():
    result = subprocess.run(
        ["npx", "--no-install", "cap", "sync"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Expected `npx cap sync` to exit 0 after the production build.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# package.json dependency
# ---------------------------------------------------------------------------


def test_splash_screen_dependency_major_is_8():
    data, _ = _read_package_json()
    deps = data.get("dependencies") or {}
    assert "@capacitor/splash-screen" in deps, (
        "Expected '@capacitor/splash-screen' to be declared in `dependencies` of "
        "package.json. It must be installed by the executor."
    )

    # Prefer the actually installed version from node_modules; fall back to the
    # declared range string when node_modules has not been refreshed.
    installed_pkg = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "splash-screen", "package.json"
    )
    if os.path.isfile(installed_pkg):
        with open(installed_pkg) as f:
            installed = json.load(f)
        version = installed.get("version", "")
    else:
        version = deps["@capacitor/splash-screen"]

    # Extract leading integer that represents the major version.
    match = re.search(r"(\d+)", version)
    assert match, (
        f"Could not parse a major version from '@capacitor/splash-screen' "
        f"version specifier '{version}'."
    )
    major = int(match.group(1))
    assert major == 8, (
        f"Expected '@capacitor/splash-screen' major version to be exactly 8; "
        f"got '{version}' (major={major})."
    )


# ---------------------------------------------------------------------------
# Capacitor config options (evaluated with tsx, regex fallback)
# ---------------------------------------------------------------------------


def test_capacitor_config_plugins_splashscreen_exact_options():
    splash = _evaluate_splashscreen_via_tsx()

    if splash is None:
        # Fallback to source-level regex on the TS/JS config; JSON should always
        # have parsed successfully above.
        config_path, fmt = _find_capacitor_config()
        if fmt == "json":
            pytest.fail(
                "capacitor.config.json must contain a plugins.SplashScreen object; "
                "none was found."
            )
        _regex_check_splashscreen(config_path)
        return

    assert isinstance(splash, dict), (
        "Capacitor config's plugins.SplashScreen must be a configuration object; got "
        f"{type(splash).__name__}."
    )

    for key, expected in REQUIRED_OPTIONS.items():
        assert key in splash, (
            f"Capacitor config plugins.SplashScreen is missing required option "
            f"'{key}'. Got keys: {sorted(splash.keys())}."
        )
        actual = splash[key]
        assert actual == expected, (
            f"Capacitor config plugins.SplashScreen.{key} must equal "
            f"{expected!r}; got {actual!r}."
        )


# ---------------------------------------------------------------------------
# TS source must import the plugin and call SplashScreen.hide()
# ---------------------------------------------------------------------------


def test_ts_source_imports_and_hides_splash_screen():
    src_dir = os.path.join(PROJECT_DIR, "src")
    assert os.path.isdir(src_dir), f"Expected a src/ directory at {src_dir}."

    import_re = re.compile(r"""from\s+['"]@capacitor/splash-screen['"]""")
    hide_re = re.compile(r"SplashScreen\s*\.\s*hide\s*\(")

    matched_files = []
    for root, _dirs, files in os.walk(src_dir):
        for name in files:
            if not name.endswith((".ts", ".tsx", ".mts", ".cts")):
                continue
            path = os.path.join(root, name)
            with open(path) as f:
                source = f.read()
            if import_re.search(source) and hide_re.search(source):
                matched_files.append(path)

    assert matched_files, (
        "Expected at least one TypeScript file under "
        f"{src_dir} to BOTH import from '@capacitor/splash-screen' AND call "
        "`SplashScreen.hide(...)`."
    )
