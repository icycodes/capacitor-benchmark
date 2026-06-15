import json
import os
import shutil
import subprocess


PROJECT_DIR = "/home/user/myproject"


def _run_build():
    """Clean any previous build outputs and run `npm run build` from scratch."""
    www_dir = os.path.join(PROJECT_DIR, "www")
    dist_dir = os.path.join(PROJECT_DIR, "dist")
    if os.path.isdir(www_dir):
        shutil.rmtree(www_dir)
    if os.path.isdir(dist_dir):
        shutil.rmtree(dist_dir)

    result = subprocess.run(
        ["npm", "run", "build"],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    return result


def test_npm_build_succeeds():
    result = _run_build()
    assert result.returncode == 0, (
        f"`npm run build` failed with code {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_vite_output_goes_to_www():
    _run_build()
    www_index = os.path.join(PROJECT_DIR, "www", "index.html")
    assert os.path.isfile(www_index), (
        f"Expected Vite build output at {www_index}, but it was not produced. "
        "Vite's `build.outDir` must be configured to `www`."
    )


def test_vite_output_does_not_go_to_dist():
    _run_build()
    dist_index = os.path.join(PROJECT_DIR, "dist", "index.html")
    assert not os.path.exists(dist_index), (
        f"Found {dist_index}; Vite must NOT build into the default `dist/` directory. "
        "Configure `build.outDir` to `www` to match Capacitor's `webDir`."
    )


def test_capacitor_config_file_exists():
    ts_cfg = os.path.join(PROJECT_DIR, "capacitor.config.ts")
    json_cfg = os.path.join(PROJECT_DIR, "capacitor.config.json")
    js_cfg = os.path.join(PROJECT_DIR, "capacitor.config.js")
    found = [p for p in (ts_cfg, json_cfg, js_cfg) if os.path.isfile(p)]
    assert found, (
        "No Capacitor config file found. Expected one of "
        f"{ts_cfg}, {json_cfg}, or {js_cfg} to exist after `npx cap init`."
    )


def test_capacitor_config_source_mentions_expected_values():
    candidates = [
        os.path.join(PROJECT_DIR, "capacitor.config.ts"),
        os.path.join(PROJECT_DIR, "capacitor.config.json"),
        os.path.join(PROJECT_DIR, "capacitor.config.js"),
    ]
    config_path = next((p for p in candidates if os.path.isfile(p)), None)
    assert config_path is not None, (
        "Expected a Capacitor config file in the project root."
    )
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    for needle in ("com.harbor.capacitor.test", "Harbor Capacitor Test", "www"):
        assert needle in content, (
            f"Expected '{needle}' to appear literally in {config_path}, "
            f"but it was not found.\nFile contents:\n{content}"
        )


def _extract_field(obj, key):
    """Recursively look up a key in a possibly-nested dict returned by `cap config --json`."""
    if isinstance(obj, dict):
        if key in obj and not isinstance(obj[key], (dict, list)):
            return obj[key]
        for v in obj.values():
            found = _extract_field(v, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _extract_field(item, key)
            if found is not None:
                return found
    return None


def test_resolved_capacitor_config_via_cli():
    cli_bin = os.path.join(PROJECT_DIR, "node_modules", ".bin", "cap")
    assert os.path.isfile(cli_bin) or os.path.islink(cli_bin), (
        f"Capacitor CLI binary not found at {cli_bin}."
    )
    result = subprocess.run(
        [cli_bin, "config", "--json"],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"`npx cap config --json` failed with code {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )

    stdout = result.stdout.strip()
    # Tolerate any leading log lines: find the first '{' and parse from there.
    brace_index = stdout.find("{")
    assert brace_index != -1, (
        f"Could not find JSON object in `cap config --json` output:\n{stdout}"
    )
    json_payload = stdout[brace_index:]
    try:
        data = json.loads(json_payload)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"`cap config --json` did not produce parseable JSON: {exc}\n"
            f"Raw output:\n{stdout}"
        )

    app_id = _extract_field(data, "appId")
    app_name = _extract_field(data, "appName")
    web_dir = _extract_field(data, "webDir")

    assert app_id == "com.harbor.capacitor.test", (
        f"Expected resolved appId to be 'com.harbor.capacitor.test', got {app_id!r}."
    )
    assert app_name == "Harbor Capacitor Test", (
        f"Expected resolved appName to be 'Harbor Capacitor Test', got {app_name!r}."
    )
    assert web_dir == "www", (
        f"Expected resolved webDir to be 'www', got {web_dir!r}."
    )
