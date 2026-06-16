import json
import os
import re
import shutil
import subprocess

PROJECT_DIR = "/home/user/myapp"


def test_node_available():
    assert shutil.which("node") is not None, "Node.js binary is not available in PATH."


def test_node_version_is_22_or_higher():
    result = subprocess.run(["node", "--version"], capture_output=True, text=True)
    assert result.returncode == 0, f"`node --version` failed: {result.stderr}"
    raw = result.stdout.strip()
    assert raw.startswith("v"), f"Unexpected node version output: {raw}"
    major = int(raw[1:].split(".")[0])
    assert major >= 22, f"Capacitor v8 requires Node.js >= 22, found {raw}."


def test_npm_available():
    assert shutil.which("npm") is not None, "npm binary is not available in PATH."


def test_npx_available():
    assert shutil.which("npx") is not None, "npx binary is not available in PATH."


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected pre-scaffolded project at {PROJECT_DIR}."
    )


def test_package_json_exists():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg), f"package.json not found at {pkg}."


def test_package_json_is_valid_json():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    assert isinstance(data, dict), "package.json must contain a JSON object."
    assert "scripts" in data, "package.json must define a 'scripts' section."


def test_capacitor_core_and_cli_preinstalled():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "@capacitor/core" in deps, (
        "Expected '@capacitor/core' to be pre-installed in the bootstrap environment."
    )
    assert "@capacitor/cli" in deps, (
        "Expected '@capacitor/cli' to be pre-installed so that `npx cap sync` can run."
    )


def test_vite_installed():
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "vite" in deps, "Expected Vite to be installed as a (dev) dependency."


def test_node_modules_installed():
    nm = os.path.join(PROJECT_DIR, "node_modules")
    assert os.path.isdir(nm), (
        f"Expected dependencies to be pre-installed at {nm}. The task starts from an "
        "already-installed Vite + Capacitor project."
    )


def test_capacitor_config_present():
    ts_path = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    json_path = os.path.join(PROJECT_DIR, "capacitor.config.json")
    assert os.path.isfile(ts_path) or os.path.isfile(json_path), (
        "Expected a Capacitor config (capacitor.config.ts or .json) to be present at "
        f"{PROJECT_DIR} before the task starts."
    )


def test_splash_screen_plugin_not_yet_installed():
    """The @capacitor/splash-screen package must NOT already be a dependency."""
    pkg = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg) as f:
        data = json.load(f)
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    assert "@capacitor/splash-screen" not in deps, (
        "The initial environment must NOT already declare '@capacitor/splash-screen'; "
        "the task is to install and wire it up."
    )

    installed_pkg = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "splash-screen", "package.json"
    )
    assert not os.path.isfile(installed_pkg), (
        "The initial environment must NOT already have '@capacitor/splash-screen' "
        f"installed at {installed_pkg}."
    )


def test_capacitor_config_has_no_splash_screen_options():
    """The Capacitor config must NOT already contain plugins.SplashScreen options."""
    ts_path = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    json_path = os.path.join(PROJECT_DIR, "capacitor.config.json")

    if os.path.isfile(json_path):
        with open(json_path) as f:
            cfg = json.load(f)
        plugins = (cfg.get("plugins") or {}) if isinstance(cfg, dict) else {}
        assert "SplashScreen" not in plugins, (
            "capacitor.config.json must NOT already configure plugins.SplashScreen."
        )

    if os.path.isfile(ts_path):
        with open(ts_path) as f:
            content = f.read()
        assert not re.search(r"SplashScreen\s*:\s*\{", content), (
            "capacitor.config.ts must NOT already contain a `SplashScreen: { ... }` "
            "block."
        )


def test_src_does_not_reference_splash_screen_plugin():
    """No TS source file should already import @capacitor/splash-screen."""
    src_dir = os.path.join(PROJECT_DIR, "src")
    assert os.path.isdir(src_dir), f"Expected a src/ directory at {src_dir}."
    import_re = re.compile(r"""from\s+['"]@capacitor/splash-screen['"]""")
    hide_re = re.compile(r"SplashScreen\s*\.\s*hide\s*\(")
    for root, _dirs, files in os.walk(src_dir):
        for name in files:
            if not name.endswith((".ts", ".tsx", ".mts", ".cts")):
                continue
            path = os.path.join(root, name)
            with open(path) as f:
                source = f.read()
            assert not import_re.search(source), (
                f"{path} must NOT already import from '@capacitor/splash-screen' in "
                "the initial state."
            )
            assert not hide_re.search(source), (
                f"{path} must NOT already call SplashScreen.hide() in the initial "
                "state."
            )
