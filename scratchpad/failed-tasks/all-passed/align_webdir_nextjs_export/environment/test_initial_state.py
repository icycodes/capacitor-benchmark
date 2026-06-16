import json
import os
import re
import shutil
import subprocess

import pytest

PROJECT_DIR = "/home/user/myapp"


def test_node_available():
    assert shutil.which("node") is not None, "node binary not found in PATH."


def test_npm_available():
    assert shutil.which("npm") is not None, "npm binary not found in PATH."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_package_json_exists_and_references_next():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), f"package.json missing at {pkg_path}."
    with open(pkg_path) as f:
        pkg = json.load(f)
    deps = {}
    deps.update(pkg.get("dependencies", {}) or {})
    deps.update(pkg.get("devDependencies", {}) or {})
    assert "next" in deps, "next is not declared as a dependency in package.json."


def test_package_json_has_build_script():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    with open(pkg_path) as f:
        pkg = json.load(f)
    scripts = pkg.get("scripts", {}) or {}
    assert "build" in scripts, "package.json is missing a 'build' script."


def test_node_modules_installed():
    nm = os.path.join(PROJECT_DIR, "node_modules")
    assert os.path.isdir(nm), (
        f"node_modules directory missing at {nm}. Dependencies were not pre-installed."
    )


def test_next_config_exists_without_static_export():
    candidates = [
        os.path.join(PROJECT_DIR, "next.config.js"),
        os.path.join(PROJECT_DIR, "next.config.mjs"),
        os.path.join(PROJECT_DIR, "next.config.ts"),
    ]
    existing = [p for p in candidates if os.path.isfile(p)]
    assert existing, (
        "Expected a next.config.{js,mjs,ts} file in the project, none were found."
    )
    pattern = re.compile(r"output\s*:\s*['\"]export['\"]")
    for path in existing:
        with open(path) as f:
            content = f.read()
        assert not pattern.search(content), (
            f"Initial {path} unexpectedly already contains output: 'export'. "
            "The bootstrap state must require the agent to add it."
        )


def test_capacitor_config_webdir_is_out():
    cap_ts = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    cap_json = os.path.join(PROJECT_DIR, "capacitor.config.json")
    path = cap_ts if os.path.isfile(cap_ts) else cap_json
    assert os.path.isfile(path), (
        f"capacitor.config.ts or capacitor.config.json must exist in {PROJECT_DIR}."
    )
    with open(path) as f:
        content = f.read()
    assert re.search(r"webDir\s*:\s*['\"]out['\"]", content), (
        f"Initial {path} must declare webDir: \"out\" so the agent only has to fix Next.js."
    )


def test_capacitor_cli_available_in_project():
    result = subprocess.run(
        ["npx", "--no-install", "cap", "--version"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"npx cap --version failed in {PROJECT_DIR}.\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )


def test_initial_build_and_sync_fails():
    # Confirm that running the existing toolchain in the bootstrap state fails,
    # i.e. the agent really does need to fix the configuration.
    out_dir = os.path.join(PROJECT_DIR, "out")
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    build = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if build.returncode != 0:
        # Build itself fails in the misconfigured state — that already proves the task
        # cannot succeed without changes. No need to attempt sync.
        return
    sync = subprocess.run(
        ["npx", "cap", "sync"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    combined = (sync.stdout or "") + "\n" + (sync.stderr or "")
    assert sync.returncode != 0 or "Could not find the web assets directory" in combined, (
        "Initial state must fail: either `npm run build` or `npx cap sync` should error "
        "before the agent fixes the configuration. Build rc="
        f"{build.returncode}, sync rc={sync.returncode}, sync output={combined}"
    )
