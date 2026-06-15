import json
import os
import shutil
import subprocess


PROJECT_DIR = "/home/user/myproject"


def test_node_binary_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npm_binary_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_npx_binary_available():
    assert shutil.which("npx") is not None, "npx binary not found in PATH."


def test_node_version_is_at_least_22():
    result = subprocess.run(
        ["node", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    version = result.stdout.strip().lstrip("v")
    major = int(version.split(".")[0])
    assert major >= 22, (
        f"Capacitor v8 requires Node.js 22 or higher, but found node version {version}."
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_package_json_exists():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), (
        f"Expected pre-existing package.json at {pkg_path}."
    )


def test_index_html_exists():
    index_path = os.path.join(PROJECT_DIR, "index.html")
    assert os.path.isfile(index_path), (
        f"Expected pre-existing Vite entry index.html at {index_path}."
    )


def test_src_main_js_exists():
    main_js = os.path.join(PROJECT_DIR, "src", "main.js")
    assert os.path.isfile(main_js), (
        f"Expected pre-existing source file at {main_js}."
    )


def test_capacitor_core_installed():
    core_pkg = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "core", "package.json"
    )
    assert os.path.isfile(core_pkg), (
        f"@capacitor/core is expected to be pre-installed; missing {core_pkg}."
    )


def test_capacitor_cli_installed():
    cli_pkg = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "cli", "package.json"
    )
    assert os.path.isfile(cli_pkg), (
        f"@capacitor/cli is expected to be pre-installed; missing {cli_pkg}."
    )


def test_vite_installed():
    vite_pkg = os.path.join(
        PROJECT_DIR, "node_modules", "vite", "package.json"
    )
    assert os.path.isfile(vite_pkg), (
        f"vite is expected to be pre-installed; missing {vite_pkg}."
    )


def test_capacitor_cli_runs():
    cli_bin = os.path.join(PROJECT_DIR, "node_modules", ".bin", "cap")
    assert os.path.isfile(cli_bin) or os.path.islink(cli_bin), (
        f"Expected Capacitor CLI binary at {cli_bin}."
    )
    result = subprocess.run(
        [cli_bin, "--version"],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"`cap --version` failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_capacitor_cli_major_version_is_8():
    cli_pkg = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "cli", "package.json"
    )
    with open(cli_pkg) as f:
        data = json.load(f)
    version = data.get("version", "")
    major = version.split(".")[0]
    assert major == "8", (
        f"Expected @capacitor/cli major version 8, but got {version!r}."
    )


def test_capacitor_not_yet_initialized():
    ts_cfg = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    json_cfg = os.path.join(PROJECT_DIR, "capacitor.config.json")
    js_cfg = os.path.join(PROJECT_DIR, "capacitor.config.js")
    assert not os.path.exists(ts_cfg), (
        f"Capacitor must NOT be pre-initialized; unexpected {ts_cfg}."
    )
    assert not os.path.exists(json_cfg), (
        f"Capacitor must NOT be pre-initialized; unexpected {json_cfg}."
    )
    assert not os.path.exists(js_cfg), (
        f"Capacitor must NOT be pre-initialized; unexpected {js_cfg}."
    )


def test_www_directory_not_pre_built():
    www_index = os.path.join(PROJECT_DIR, "www", "index.html")
    assert not os.path.exists(www_index), (
        f"`www/index.html` must not exist before the executor runs; found {www_index}."
    )
