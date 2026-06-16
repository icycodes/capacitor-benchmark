import json
import os
import re
import subprocess

PROJECT_DIR = "/home/user/myapp"
SNAPSHOT_PATH = "/home/user/.harbor/initial_capacitor_config.json"


def _parse_major(version_string: str) -> int:
    """Parse the major version from an npm version string or range.

    Strips leading semver range operators (^, ~, >=, >, =, whitespace, optional
    leading 'v') and parses the first dotted segment as an integer.
    """
    assert isinstance(version_string, str), (
        f"Expected version to be a string, got {type(version_string).__name__}."
    )
    cleaned = version_string.strip()
    for prefix in (">=", "<=", "==", "^", "~", ">", "<", "="):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].lstrip()
            break
    if cleaned.startswith("v") or cleaned.startswith("V"):
        cleaned = cleaned[1:]
    match = re.match(r"(\d+)", cleaned)
    assert match is not None, (
        f"Could not parse a major version number from version string {version_string!r}."
    )
    return int(match.group(1))


def _load_package_json():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), f"package.json not found at {pkg_path}."
    with open(pkg_path) as f:
        return json.load(f), pkg_path


# ---------------------------------------------------------------------------
# 1. EVERY @capacitor/* dependency/devDependency declared in package.json is v8.
# ---------------------------------------------------------------------------


def test_every_capacitor_specifier_in_package_json_is_v8():
    pkg, pkg_path = _load_package_json()
    deps = {}
    deps.update(pkg.get("dependencies", {}) or {})
    deps.update(pkg.get("devDependencies", {}) or {})
    capacitor_keys = sorted(k for k in deps if k.startswith("@capacitor/"))
    assert capacitor_keys, (
        f"Expected at least one '@capacitor/*' dependency in {pkg_path}, found none."
    )
    # The bootstrap pins these specific packages; they MUST still be declared.
    required = {"@capacitor/core", "@capacitor/cli", "@capacitor/preferences"}
    missing = sorted(required - set(capacitor_keys))
    assert not missing, (
        f"Expected the following @capacitor/* packages to remain declared in "
        f"{pkg_path}: {missing}. Found: {capacitor_keys}"
    )
    for key in capacitor_keys:
        declared = deps[key]
        major = _parse_major(declared)
        assert major == 8, (
            f"Expected the '{key}' specifier in {pkg_path} to resolve to a "
            f"Capacitor v8 release, but its declared range is {declared!r} "
            f"(parsed major = {major})."
        )


# ---------------------------------------------------------------------------
# 2-4. Installed @capacitor/core, @capacitor/cli, @capacitor/preferences are v8.
# ---------------------------------------------------------------------------


def _assert_installed_major_eight(package_name: str):
    pkg_path = os.path.join(
        PROJECT_DIR, "node_modules", "@capacitor", package_name, "package.json"
    )
    assert os.path.isfile(pkg_path), (
        f"Expected installed '@capacitor/{package_name}' package.json at "
        f"{pkg_path}; the executor must reinstall after upgrading the version "
        f"specifier."
    )
    with open(pkg_path) as f:
        meta = json.load(f)
    version = meta.get("version")
    assert isinstance(version, str), (
        f"Expected a string 'version' field in {pkg_path}, got {version!r}."
    )
    major = _parse_major(version)
    assert major == 8, (
        f"Installed @capacitor/{package_name} version must be on the 8.x major; "
        f"found version {version!r} (parsed major = {major}) at {pkg_path}."
    )


def test_installed_capacitor_core_is_v8():
    _assert_installed_major_eight("core")


def test_installed_capacitor_cli_is_v8():
    _assert_installed_major_eight("cli")


def test_installed_capacitor_preferences_is_v8():
    _assert_installed_major_eight("preferences")


# ---------------------------------------------------------------------------
# 5. Every other @capacitor/* package directory installed under node_modules
#    must also be on v8 (in case the executor adds more plugins or one is
#    pulled transitively).
# ---------------------------------------------------------------------------


def test_all_installed_capacitor_packages_are_v8():
    cap_dir = os.path.join(PROJECT_DIR, "node_modules", "@capacitor")
    assert os.path.isdir(cap_dir), (
        f"Expected {cap_dir} to exist after the upgrade. The executor must run "
        f"`npm install` after bumping the @capacitor/* specifiers."
    )
    entries = [
        name for name in os.listdir(cap_dir)
        if os.path.isdir(os.path.join(cap_dir, name))
    ]
    assert entries, (
        f"Expected at least one installed @capacitor/* package directory under "
        f"{cap_dir}, found none."
    )
    failures = []
    for name in sorted(entries):
        pkg_path = os.path.join(cap_dir, name, "package.json")
        if not os.path.isfile(pkg_path):
            # Skip non-package directories (e.g. cache leftovers); they do not
            # contribute a usable plugin version.
            continue
        with open(pkg_path) as f:
            meta = json.load(f)
        version = meta.get("version")
        if not isinstance(version, str):
            failures.append(
                f"  - @capacitor/{name}: missing string 'version' field "
                f"(got {version!r})"
            )
            continue
        major = _parse_major(version)
        if major != 8:
            failures.append(
                f"  - @capacitor/{name}: installed version {version!r} "
                f"(parsed major = {major}) is NOT on the 8.x major."
            )
    assert not failures, (
        "Every installed '@capacitor/*' package must be on the 8.x major after "
        "the upgrade. Found the following violations:\n" + "\n".join(failures)
    )


# ---------------------------------------------------------------------------
# 6. package-lock.json exists and was regenerated.
# ---------------------------------------------------------------------------


def test_package_lock_exists_and_was_regenerated():
    lock_path = os.path.join(PROJECT_DIR, "package-lock.json")
    assert os.path.isfile(lock_path), (
        f"Expected {lock_path} to exist after `npm install`. The executor must "
        f"reinstall after upgrading the @capacitor/* version specifiers so the "
        f"lockfile is regenerated."
    )
    with open(lock_path) as f:
        lock = json.load(f)
    assert isinstance(lock, dict), (
        f"Expected {lock_path} to contain a JSON object."
    )
    assert "lockfileVersion" in lock, (
        f"Expected {lock_path} to contain a 'lockfileVersion' field. Found "
        f"keys: {sorted(lock.keys())}"
    )


# ---------------------------------------------------------------------------
# 7. `npm run build` exits 0 and produces dist/index.html.
# ---------------------------------------------------------------------------


def test_npm_run_build_succeeds_and_produces_dist_index_html():
    dist_dir = os.path.join(PROJECT_DIR, "dist")
    # Remove stale build artifacts so this measures a fresh build performed
    # after the upgrade.
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
        "Expected `npm run build` to exit 0 in /home/user/myapp after the "
        "Capacitor v8 upgrade.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    dist_index = os.path.join(dist_dir, "index.html")
    assert os.path.isfile(dist_index), (
        f"Expected production build output at {dist_index} after `npm run build`."
    )


# ---------------------------------------------------------------------------
# 8. `npx cap sync` exits 0 with NO "version mismatch" warning.
# ---------------------------------------------------------------------------


def test_npx_cap_sync_exits_zero_with_no_version_mismatch_warning():
    result = subprocess.run(
        ["npx", "--no-install", "cap", "sync"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Expected `npx cap sync` to exit 0 in /home/user/myapp after the "
        "Capacitor v8 upgrade.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    combined = ((result.stdout or "") + "\n" + (result.stderr or "")).lower()
    assert "version mismatch" not in combined, (
        "Expected `npx cap sync` output to NOT contain a 'version mismatch' "
        "warning. The Capacitor CLI emits this when a @capacitor/* plugin "
        "major version disagrees with the CLI's major version; every plugin "
        "MUST be upgraded in lock-step to v8.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# 9. capacitor.config.ts appId/appName/webDir are unchanged.
# ---------------------------------------------------------------------------


def _extract_capacitor_config_string_field(text: str, field: str) -> str:
    """Extract a string-valued top-level field from a capacitor.config.ts file.

    Matches both single- and double-quoted forms, tolerates extra whitespace.
    """
    pattern = rf"{field}\s*:\s*['\"]([^'\"]+)['\"]"
    match = re.search(pattern, text)
    assert match is not None, (
        f"Could not locate '{field}' in capacitor.config.ts. The file must "
        f"declare it as a quoted string."
    )
    return match.group(1)


def test_capacitor_config_app_id_app_name_webdir_unchanged():
    assert os.path.isfile(SNAPSHOT_PATH), (
        f"Expected initial Capacitor config snapshot at {SNAPSHOT_PATH}. "
        f"This file is written by the environment Dockerfile and is required "
        f"to verify the executor did not change appId/appName/webDir."
    )
    with open(SNAPSHOT_PATH) as f:
        snapshot = json.load(f)

    cap_config = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    assert os.path.isfile(cap_config), (
        f"Expected the Capacitor config file at {cap_config} to still exist "
        f"after the upgrade."
    )
    with open(cap_config) as f:
        text = f.read()

    current_app_id = _extract_capacitor_config_string_field(text, "appId")
    current_app_name = _extract_capacitor_config_string_field(text, "appName")
    current_web_dir = _extract_capacitor_config_string_field(text, "webDir")

    assert current_app_id == snapshot["appId"], (
        f"Expected capacitor.config.ts `appId` to remain {snapshot['appId']!r} "
        f"from the bootstrap snapshot, but found {current_app_id!r}."
    )
    assert current_app_name == snapshot["appName"], (
        f"Expected capacitor.config.ts `appName` to remain {snapshot['appName']!r} "
        f"from the bootstrap snapshot, but found {current_app_name!r}."
    )
    assert current_web_dir == snapshot["webDir"], (
        f"Expected capacitor.config.ts `webDir` to remain {snapshot['webDir']!r} "
        f"from the bootstrap snapshot, but found {current_web_dir!r}."
    )
