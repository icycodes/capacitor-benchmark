import json
import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myproject"


def test_node_available():
    assert shutil.which("node") is not None, "node is not available in PATH."


def test_npx_available():
    assert shutil.which("npx") is not None, "npx is not available in PATH."


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_package_json_exists():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), f"package.json missing at {pkg_path}."


def test_capacitor_core_installed():
    pkg_path = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "core", "package.json")
    assert os.path.isfile(pkg_path), (
        f"@capacitor/core is not installed under {PROJECT_DIR}/node_modules."
    )
    with open(pkg_path) as f:
        data = json.load(f)
    version = str(data.get("version", ""))
    assert version.startswith("8."), (
        f"@capacitor/core must be v8.x for this task; got version {version!r}."
    )


def test_capacitor_cli_installed():
    pkg_path = os.path.join(PROJECT_DIR, "node_modules", "@capacitor", "cli", "package.json")
    assert os.path.isfile(pkg_path), (
        f"@capacitor/cli is not installed under {PROJECT_DIR}/node_modules."
    )


def test_typescript_available_in_project():
    tsc_path = os.path.join(PROJECT_DIR, "node_modules", ".bin", "tsc")
    assert os.path.isfile(tsc_path) or os.path.islink(tsc_path), (
        f"TypeScript compiler is not available at {tsc_path}."
    )


def test_capacitor_config_present():
    config_path = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    assert os.path.isfile(config_path), (
        f"Expected starter capacitor.config.ts at {config_path}."
    )
    with open(config_path) as f:
        content = f.read()
    # The starter must NOT already enable CapacitorCookies; this is what the executor needs to do.
    normalized = content.replace(" ", "").replace("\n", "")
    assert "CapacitorCookies" not in normalized, (
        "Starter capacitor.config.ts should not pre-enable CapacitorCookies; "
        "the executor is expected to add this configuration."
    )


def test_tsconfig_present():
    tsconfig_path = os.path.join(PROJECT_DIR, "tsconfig.json")
    assert os.path.isfile(tsconfig_path), f"Missing tsconfig.json at {tsconfig_path}."


def test_src_dir_present_and_session_not_yet_written():
    src_dir = os.path.join(PROJECT_DIR, "src")
    assert os.path.isdir(src_dir), f"Source directory {src_dir} missing."
    session_path = os.path.join(src_dir, "auth", "session.ts")
    assert not os.path.exists(session_path), (
        f"src/auth/session.ts must not exist initially; the executor must create it. "
        f"Found pre-existing file at {session_path}."
    )


def test_verifier_assets_present():
    # The Docker image installs the verifier harness alongside the project.
    verifier_dir = "/home/user/verifier"
    assert os.path.isdir(verifier_dir), f"Verifier directory missing at {verifier_dir}."
    for fname in ("verify_session.mjs", "server.mjs", "run_session_check.sh"):
        path = os.path.join(verifier_dir, fname)
        assert os.path.isfile(path), f"Missing verifier asset: {path}."


def test_tsc_can_parse_starter_project():
    # The starter project (without session.ts) must already type-check.
    result = subprocess.run(
        ["npx", "tsc", "--noEmit"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        "Starter project failed initial tsc --noEmit; "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}."
    )
