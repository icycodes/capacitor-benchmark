import json
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

PROJECT_DIR = "/home/user/myapp"
ANDROID_APP_MAIN = os.path.join(PROJECT_DIR, "android", "app", "src", "main")
CAPACITOR_CONFIG = os.path.join(PROJECT_DIR, "capacitor.config.ts")
ANDROID_MANIFEST = os.path.join(ANDROID_APP_MAIN, "AndroidManifest.xml")
NETWORK_SECURITY_XML = os.path.join(
    ANDROID_APP_MAIN, "res", "xml", "network_security_config.xml"
)
SYNC_LOG = os.path.join(PROJECT_DIR, "sync.log")
VERIFY_SYNC_LOG = os.path.join(PROJECT_DIR, "verify-sync.log")
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


def _load_capacitor_config_as_object():
    """Transpile the TypeScript config file and load its default export as JSON."""
    work_dir = tempfile.mkdtemp(prefix="cap-cfg-")
    # Transpile capacitor.config.ts -> CommonJS in a tempdir using the local TS toolchain.
    compile_proc = subprocess.run(
        [
            "npx",
            "--yes",
            "-p",
            "typescript@5",
            "tsc",
            "--target",
            "ES2019",
            "--module",
            "commonjs",
            "--esModuleInterop",
            "--skipLibCheck",
            "--outDir",
            work_dir,
            CAPACITOR_CONFIG,
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert compile_proc.returncode == 0, (
        "Failed to transpile capacitor.config.ts: "
        f"stdout={compile_proc.stdout!r} stderr={compile_proc.stderr!r}"
    )
    compiled = os.path.join(work_dir, "capacitor.config.js")
    assert os.path.isfile(compiled), (
        f"Expected compiled config at {compiled}. dir contents: {os.listdir(work_dir)}"
    )
    node_proc = subprocess.run(
        [
            "node",
            "-e",
            (
                "const m = require(process.argv[1]); "
                "process.stdout.write(JSON.stringify(m.default ?? m));"
            ),
            compiled,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert node_proc.returncode == 0, (
        "Failed to evaluate compiled capacitor config: "
        f"stdout={node_proc.stdout!r} stderr={node_proc.stderr!r}"
    )
    try:
        return json.loads(node_proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            "Compiled capacitor.config.ts did not export a JSON-serialisable object. "
            f"stdout={node_proc.stdout!r} error={exc}"
        )


def test_capacitor_config_server_block_set():
    config = _load_capacitor_config_as_object()
    assert isinstance(config, dict), (
        f"capacitor.config.ts default export must be an object, got: {type(config)}"
    )
    assert config.get("appId") == "com.example.myapp", (
        f"appId must be preserved as 'com.example.myapp', got: {config.get('appId')!r}"
    )
    assert config.get("appName") == "My Native App", (
        "appName must be preserved as 'My Native App', got: "
        f"{config.get('appName')!r}"
    )
    assert config.get("webDir") == "dist", (
        f"webDir must be preserved as 'dist', got: {config.get('webDir')!r}"
    )
    server = config.get("server")
    assert isinstance(server, dict), (
        f"`server` block must be an object in capacitor.config.ts, got: {server!r}"
    )
    assert server.get("androidScheme") == "https", (
        "server.androidScheme must be 'https', got: "
        f"{server.get('androidScheme')!r}"
    )
    assert server.get("hostname") == "myapp.example.com", (
        "server.hostname must be 'myapp.example.com', got: "
        f"{server.get('hostname')!r}"
    )


def test_network_security_config_file_exists():
    assert os.path.isfile(NETWORK_SECURITY_XML), (
        f"Expected network security config at {NETWORK_SECURITY_XML}."
    )


def test_network_security_config_permits_cleartext_only_for_localhost():
    tree = ET.parse(NETWORK_SECURITY_XML)
    root = tree.getroot()
    assert root.tag == "network-security-config", (
        "Root element of network_security_config.xml must be "
        f"<network-security-config>, got: <{root.tag}>"
    )

    # base-config must not globally permit cleartext.
    for base in root.findall("base-config"):
        if base.get("cleartextTrafficPermitted", "").lower() == "true":
            raise AssertionError(
                "<base-config cleartextTrafficPermitted=\"true\"> must NOT be present "
                "— cleartext should only be permitted per-domain (localhost)."
            )

    found_localhost = False
    for dc in root.findall("domain-config"):
        cleartext_attr = dc.get("cleartextTrafficPermitted", "").lower()
        if cleartext_attr != "true":
            continue
        for dom in dc.findall("domain"):
            text = (dom.text or "").strip()
            if text == "localhost":
                include_subdomains = dom.get("includeSubdomains")
                if include_subdomains is not None:
                    assert include_subdomains.lower() == "false", (
                        "If `includeSubdomains` is set on the localhost <domain>, "
                        f"it must be 'false', got: {include_subdomains!r}"
                    )
                found_localhost = True
                break
        if found_localhost:
            break

    assert found_localhost, (
        "Expected a <domain-config cleartextTrafficPermitted=\"true\"> "
        "containing a <domain>localhost</domain> entry in "
        f"{NETWORK_SECURITY_XML}."
    )


def test_android_manifest_references_network_security_config():
    tree = ET.parse(ANDROID_MANIFEST)
    root = tree.getroot()
    application = root.find("application")
    assert application is not None, (
        "AndroidManifest.xml must contain an <application> element."
    )
    nsc = application.get(f"{ANDROID_NS}networkSecurityConfig")
    assert nsc == "@xml/network_security_config", (
        "<application android:networkSecurityConfig> must be "
        f"'@xml/network_security_config', got: {nsc!r}"
    )

    # Make sure the existing MainActivity entry is still present (unchanged structure).
    activities = application.findall("activity")
    activity_names = [a.get(f"{ANDROID_NS}name") for a in activities]
    assert any(
        name and name.endswith("MainActivity") for name in activity_names
    ), (
        "AndroidManifest.xml must still declare the MainActivity activity. "
        f"Found activity names: {activity_names!r}"
    )


def test_sync_log_records_successful_sync():
    assert os.path.isfile(SYNC_LOG), (
        f"Sync log {SYNC_LOG} must exist (capture of `npx cap sync android`)."
    )
    with open(SYNC_LOG, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    assert content.strip(), f"Sync log {SYNC_LOG} must not be empty."
    assert re.search(r"[Ss]ync finished", content), (
        "Sync log must contain a 'Sync finished' line indicating a "
        f"successful `npx cap sync android` run. Log content: {content!r}"
    )


def test_npx_cap_sync_android_runs_cleanly():
    """Re-run `npx cap sync android` to confirm the config is valid and idempotent."""
    if os.path.exists(VERIFY_SYNC_LOG):
        os.remove(VERIFY_SYNC_LOG)
    with open(VERIFY_SYNC_LOG, "w", encoding="utf-8") as logf:
        proc = subprocess.run(
            ["npx", "--no-install", "cap", "sync", "android"],
            cwd=PROJECT_DIR,
            stdout=logf,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=600,
        )
    with open(VERIFY_SYNC_LOG, "r", encoding="utf-8", errors="replace") as f:
        log = f.read()
    assert proc.returncode == 0, (
        "`npx cap sync android` must exit 0 after the fix. "
        f"exit={proc.returncode} log={log!r}"
    )
    assert re.search(r"[Ss]ync finished", log), (
        "Verifier re-run of `npx cap sync android` must report 'Sync finished'. "
        f"Log: {log!r}"
    )


def test_server_config_still_present_after_resync():
    """After a fresh sync, the config file must still hold the required server block."""
    config = _load_capacitor_config_as_object()
    server = config.get("server") if isinstance(config, dict) else None
    assert isinstance(server, dict), (
        "After re-running `npx cap sync android`, capacitor.config.ts must still "
        f"declare a server block. Got server={server!r}."
    )
    assert server.get("androidScheme") == "https", (
        "server.androidScheme must remain 'https' after re-sync."
    )
    assert server.get("hostname") == "myapp.example.com", (
        "server.hostname must remain 'myapp.example.com' after re-sync."
    )


def test_network_security_xml_still_present_after_resync():
    assert os.path.isfile(NETWORK_SECURITY_XML), (
        "network_security_config.xml must persist after `npx cap sync android` "
        "is re-run by the verifier."
    )


def test_android_manifest_still_references_nsc_after_resync():
    tree = ET.parse(ANDROID_MANIFEST)
    root = tree.getroot()
    application = root.find("application")
    assert application is not None
    nsc = application.get(f"{ANDROID_NS}networkSecurityConfig")
    assert nsc == "@xml/network_security_config", (
        "AndroidManifest.xml must still reference @xml/network_security_config "
        "after the verifier re-runs `npx cap sync android`."
    )
