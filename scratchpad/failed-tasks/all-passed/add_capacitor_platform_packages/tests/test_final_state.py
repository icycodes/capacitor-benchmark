import json
import os
import re
import subprocess

PROJECT_DIR = "/home/user/myapp"


def _parse_major(version_string: str) -> int:
    """Parse the major version from an npm version string or range.

    Strips leading semver range operators (^, ~, >=, >, =, whitespace) and
    parses the first dotted segment as an integer.
    """
    assert isinstance(version_string, str), (
        f"Expected version to be a string, got {type(version_string).__name__}."
    )
    cleaned = version_string.strip()
    # Strip a leading range operator. Order matters: check 2-char operators first.
    for prefix in (">=", "<=", "==", "^", "~", ">", "<", "="):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].lstrip()
            break
    # Drop a leading 'v' if present (e.g. "v8.4.0").
    if cleaned.startswith("v") or cleaned.startswith("V"):
        cleaned = cleaned[1:]
    match = re.match(r"(\d+)", cleaned)
    assert match is not None, (
        f"Could not parse a major version number from version string {version_string!r}."
    )
    return int(match.group(1))


# ---------------------------------------------------------------------------
# package.json dependency declarations
# ---------------------------------------------------------------------------


def _load_package_json():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), f"package.json not found at {pkg_path}."
    with open(pkg_path) as f:
        return json.load(f), pkg_path


def test_package_json_declares_capacitor_android_in_dependencies():
    pkg, pkg_path = _load_package_json()
    deps = pkg.get("dependencies", {}) or {}
    assert "@capacitor/android" in deps, (
        f"Expected '@capacitor/android' to appear in the 'dependencies' map of "
        f"{pkg_path}. Found dependencies keys: {sorted(deps)}"
    )
    declared = deps["@capacitor/android"]
    major = _parse_major(declared)
    assert major == 8, (
        f"Expected '@capacitor/android' dependency in {pkg_path} to resolve to a "
        f"Capacitor v8 release, but its declared range is {declared!r} (parsed major "
        f"= {major})."
    )


def test_package_json_declares_capacitor_ios_in_dependencies():
    pkg, pkg_path = _load_package_json()
    deps = pkg.get("dependencies", {}) or {}
    assert "@capacitor/ios" in deps, (
        f"Expected '@capacitor/ios' to appear in the 'dependencies' map of "
        f"{pkg_path}. Found dependencies keys: {sorted(deps)}"
    )
    declared = deps["@capacitor/ios"]
    major = _parse_major(declared)
    assert major == 8, (
        f"Expected '@capacitor/ios' dependency in {pkg_path} to resolve to a "
        f"Capacitor v8 release, but its declared range is {declared!r} (parsed major "
        f"= {major})."
    )


# ---------------------------------------------------------------------------
# Installed package presence + version
# ---------------------------------------------------------------------------


def test_capacitor_android_node_module_installed_with_v8():
    pkg_path = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "android", "package.json"
    )
    assert os.path.isfile(pkg_path), (
        f"Expected installed '@capacitor/android' package.json at {pkg_path}; "
        "the executor must run `npm install @capacitor/android@<v8>` (or equivalent)."
    )
    with open(pkg_path) as f:
        meta = json.load(f)
    version = meta.get("version")
    assert isinstance(version, str), (
        f"Expected a string 'version' field in {pkg_path}, got {version!r}."
    )
    major = _parse_major(version)
    assert major == 8, (
        f"Installed @capacitor/android version must be on the 8.x major; "
        f"found version {version!r} (parsed major = {major}) at {pkg_path}."
    )


def test_capacitor_ios_node_module_installed_with_v8():
    pkg_path = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", "ios", "package.json"
    )
    assert os.path.isfile(pkg_path), (
        f"Expected installed '@capacitor/ios' package.json at {pkg_path}; "
        "the executor must run `npm install @capacitor/ios@<v8>` (or equivalent)."
    )
    with open(pkg_path) as f:
        meta = json.load(f)
    version = meta.get("version")
    assert isinstance(version, str), (
        f"Expected a string 'version' field in {pkg_path}, got {version!r}."
    )
    major = _parse_major(version)
    assert major == 8, (
        f"Installed @capacitor/ios version must be on the 8.x major; "
        f"found version {version!r} (parsed major = {major}) at {pkg_path}."
    )


# ---------------------------------------------------------------------------
# Build + sync end-to-end
# ---------------------------------------------------------------------------


def test_npm_run_build_succeeds_and_produces_dist_index_html():
    dist_dir = os.path.join(PROJECT_DIR, "dist")
    # Remove stale build artifacts so this assertion measures a fresh build
    # performed after the executor installed the platform packages.
    if os.path.isdir(dist_dir):
        subprocess.run(["rm", "-rf", dist_dir], check=True)

    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Expected `npm run build` to exit 0 in /home/user/myapp.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    dist_index = os.path.join(dist_dir, "index.html")
    assert os.path.isfile(dist_index), (
        f"Expected production build output at {dist_index} after `npm run build`."
    )


def test_npx_cap_sync_exits_zero():
    result = subprocess.run(
        ["npx", "--no-install", "cap", "sync"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Expected `npx cap sync` to exit 0 in /home/user/myapp after the platform "
        "packages were installed.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
