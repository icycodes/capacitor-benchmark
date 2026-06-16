import json
import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myproject"


def test_node_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npm_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_npx_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH."


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_package_json_exists():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), (
        f"package.json not found at {pkg_path}."
    )


def test_node_modules_installed():
    nm_path = os.path.join(PROJECT_DIR, "node_modules")
    assert os.path.isdir(nm_path), (
        f"node_modules directory not present at {nm_path}; "
        "dependencies should be pre-installed."
    )


def test_capacitor_core_dependency_installed():
    core_path = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "core")
    assert os.path.isdir(core_path), (
        f"@capacitor/core is not installed under {core_path}."
    )


def test_capacitor_cli_dependency_installed():
    cli_path = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "cli")
    assert os.path.isdir(cli_path), (
        f"@capacitor/cli is not installed under {cli_path}."
    )


def test_capacitor_preferences_dependency_installed():
    pref_path = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "preferences"
    )
    assert os.path.isdir(pref_path), (
        f"@capacitor/preferences is not installed under {pref_path}."
    )


def test_typescript_compiler_available():
    tsc_bin = os.path.join(PROJECT_DIR, "node_modules", ".bin", "tsc")
    assert os.path.isfile(tsc_bin), (
        f"TypeScript compiler binary not found at {tsc_bin}."
    )


def test_capacitor_config_exists():
    config_path = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    assert os.path.isfile(config_path), (
        f"capacitor.config.ts not found at {config_path}."
    )


def test_capacitor_config_has_required_fields():
    config_path = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    with open(config_path) as f:
        content = f.read()
    assert "com.example.myapp" in content, (
        "capacitor.config.ts should contain the initial appId 'com.example.myapp'."
    )
    assert "My Native App" in content, (
        "capacitor.config.ts should contain the initial appName 'My Native App'."
    )
    assert "dist" in content, (
        "capacitor.config.ts should contain the initial webDir 'dist'."
    )


def test_capacitor_http_not_yet_enabled():
    config_path = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    with open(config_path) as f:
        content = f.read()
    assert "CapacitorHttp" not in content, (
        "capacitor.config.ts should NOT yet enable CapacitorHttp in the initial state."
    )


def test_tsconfig_exists():
    tsconfig_path = os.path.join(PROJECT_DIR, "tsconfig.json")
    assert os.path.isfile(tsconfig_path), (
        f"tsconfig.json not found at {tsconfig_path}."
    )


def test_src_directory_exists():
    src_path = os.path.join(PROJECT_DIR, "src")
    assert os.path.isdir(src_path), (
        f"src directory not found at {src_path}."
    )


def test_http_client_module_not_yet_present():
    helper_path = os.path.join(PROJECT_DIR, "src", "api", "httpClient.ts")
    assert not os.path.exists(helper_path), (
        f"{helper_path} must not exist in the initial state; "
        "the executor is expected to create it."
    )


def test_build_script_defined():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg_path) as f:
        pkg = json.load(f)
    scripts = pkg.get("scripts", {})
    assert "build" in scripts, (
        "package.json must define a 'build' script (configured to run tsc --noEmit)."
    )


def test_capacitor_cli_runs():
    result = subprocess.run(
        ["npx", "--no-install", "cap", "--version"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"`npx cap --version` failed in {PROJECT_DIR}. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
