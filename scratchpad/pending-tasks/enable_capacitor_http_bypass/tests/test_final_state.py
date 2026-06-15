import json
import os
import re
import subprocess

import pytest

PROJECT_DIR = "/home/user/myproject"
CAPACITOR_CONFIG = os.path.join(PROJECT_DIR, "capacitor.config.ts")
CLI_SCRIPT = os.path.join(PROJECT_DIR, "scripts", "http-cli.ts")


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable must be set for verification."
    return run_id


# ---------------------------------------------------------------------------
# 1. CapacitorHttp config check
# ---------------------------------------------------------------------------

def test_capacitor_config_enables_http_plugin():
    """Parse capacitor.config.ts via tsx and verify plugins.CapacitorHttp.enabled === true."""
    assert os.path.isfile(CAPACITOR_CONFIG), (
        f"capacitor.config.ts not found at {CAPACITOR_CONFIG}."
    )

    eval_script = (
        "import('./capacitor.config.ts').then(m => {"
        "  const cfg = m.default ?? m.config ?? m;"
        "  process.stdout.write(JSON.stringify(cfg));"
        "}).catch(err => { console.error(err); process.exit(1); });"
    )
    result = subprocess.run(
        ["npx", "tsx", "-e", eval_script],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"Failed to evaluate capacitor.config.ts via tsx. "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )

    try:
        cfg = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"capacitor.config.ts did not export a JSON-serializable config object: "
            f"{exc}; raw output: {result.stdout!r}"
        )

    plugins = cfg.get("plugins", {}) if isinstance(cfg, dict) else {}
    cap_http = plugins.get("CapacitorHttp")
    assert isinstance(cap_http, dict), (
        f"capacitor.config.ts must define plugins.CapacitorHttp as an object; got: {cap_http!r}"
    )
    assert cap_http.get("enabled") is True, (
        f"plugins.CapacitorHttp.enabled must be exactly `true`; got: {cap_http.get('enabled')!r}"
    )


# ---------------------------------------------------------------------------
# 2. No forbidden HTTP libraries / direct fetch usage
# ---------------------------------------------------------------------------

def test_cli_script_exists():
    assert os.path.isfile(CLI_SCRIPT), (
        f"scripts/http-cli.ts not found at {CLI_SCRIPT}."
    )


def test_cli_imports_capacitor_http_and_avoids_forbidden_clients():
    with open(CLI_SCRIPT, "r", encoding="utf-8") as f:
        src = f.read()

    assert re.search(
        r"""import\s*\{[^}]*\bCapacitorHttp\b[^}]*\}\s*from\s*['"]@capacitor/core['"]""",
        src,
    ), (
        "scripts/http-cli.ts must `import { CapacitorHttp } from '@capacitor/core'` "
        "(or include CapacitorHttp in a named import from @capacitor/core)."
    )

    forbidden_patterns = [
        r"""from\s*['"]axios['"]""",
        r"""from\s*['"]node-fetch['"]""",
        r"""require\(\s*['"]axios['"]\s*\)""",
        r"""require\(\s*['"]node-fetch['"]\s*\)""",
        r"""require\(\s*['"]https?['"]\s*\)""",
        r"""from\s*['"]node:https?['"]""",
        r"""from\s*['"]https?['"]""",
    ]
    for pat in forbidden_patterns:
        assert not re.search(pat, src), (
            f"scripts/http-cli.ts must not use forbidden HTTP client matching pattern {pat!r}; "
            "all outbound requests must go through CapacitorHttp."
        )

    # Strip line/block comments before checking for a bare `fetch(` usage.
    stripped = re.sub(r"//.*", "", src)
    stripped = re.sub(r"/\*.*?\*/", "", stripped, flags=re.DOTALL)
    assert not re.search(r"(?<![A-Za-z0-9_$.])fetch\s*\(", stripped), (
        "scripts/http-cli.ts must not call `fetch(` directly; route requests through CapacitorHttp."
    )


# ---------------------------------------------------------------------------
# 3. GET smoke test against httpbin.org
# ---------------------------------------------------------------------------

def _run_cli(args, timeout=120):
    cmd = ["npx", "tsx", "scripts/http-cli.ts"] + args
    return subprocess.run(
        cmd,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _parse_stdout(stdout: str):
    lines = [ln for ln in stdout.splitlines() if ln.strip() != ""]
    assert len(lines) >= 2, (
        f"Expected at least two non-empty stdout lines (status + JSON body); got: {stdout!r}"
    )
    status_line = lines[0].strip()
    body_line = lines[1].strip()

    m = re.match(r"^Status:\s*(\d+)$", status_line)
    assert m, f"First stdout line must match 'Status: <code>'; got: {status_line!r}"
    status_code = int(m.group(1))

    try:
        body = json.loads(body_line)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"Second stdout line must be a JSON object; got: {body_line!r} ({exc})"
        )

    return status_code, body


def test_cli_get_forwards_header_and_query():
    run_id = _run_id()
    url = f"https://httpbin.org/get?run={run_id}"
    header = f"X-Zealt-Run:{run_id}"
    result = _run_cli([
        "--method", "GET",
        "--url", url,
        "--header", header,
    ])
    assert result.returncode == 0, (
        f"GET CLI invocation failed. stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    status_code, body = _parse_stdout(result.stdout)
    assert status_code == 200, f"Expected status 200 from httpbin GET; got {status_code}."

    args = body.get("args") or {}
    assert args.get("run") == run_id, (
        f"httpbin response should echo back ?run={run_id} in args; got args={args!r}"
    )

    headers = body.get("headers") or {}
    # httpbin canonicalizes header names — match case-insensitively just in case.
    found = None
    for k, v in headers.items():
        if k.lower() == "x-zealt-run":
            found = v
            break
    assert found == run_id, (
        f"httpbin response should echo back X-Zealt-Run={run_id}; got header={found!r}, all headers={headers!r}"
    )


# ---------------------------------------------------------------------------
# 4. POST smoke test against httpbin.org
# ---------------------------------------------------------------------------

def test_cli_post_forwards_body_and_header():
    run_id = _run_id()
    body_payload = {"runId": run_id, "hello": "capacitor"}
    result = _run_cli([
        "--method", "POST",
        "--url", "https://httpbin.org/post",
        "--body", json.dumps(body_payload),
        "--header", f"X-Zealt-Run:{run_id}",
    ])
    assert result.returncode == 0, (
        f"POST CLI invocation failed. stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    status_code, body = _parse_stdout(result.stdout)
    assert status_code == 200, f"Expected status 200 from httpbin POST; got {status_code}."

    json_field = body.get("json")
    assert isinstance(json_field, dict), (
        f"httpbin POST response should contain a parsed `json` object; got: {json_field!r}"
    )
    assert json_field.get("runId") == run_id, (
        f"Expected echoed body.json.runId == {run_id}; got {json_field.get('runId')!r}"
    )
    assert json_field.get("hello") == "capacitor", (
        f"Expected echoed body.json.hello == 'capacitor'; got {json_field.get('hello')!r}"
    )

    headers = body.get("headers") or {}
    found = None
    for k, v in headers.items():
        if k.lower() == "x-zealt-run":
            found = v
            break
    assert found == run_id, (
        f"Expected echoed X-Zealt-Run header == {run_id}; got {found!r}; all headers={headers!r}"
    )


# ---------------------------------------------------------------------------
# 5. Non-2xx responses still report a deterministic status line
# ---------------------------------------------------------------------------

def test_cli_reports_non_2xx_status():
    result = _run_cli([
        "--method", "GET",
        "--url", "https://httpbin.org/status/500",
    ])
    # The CLI may exit 0 or non-zero, but the first stdout line must still be a deterministic
    # `Status: 500`.
    lines = [ln for ln in result.stdout.splitlines() if ln.strip() != ""]
    assert lines, (
        f"CLI produced no stdout for a 500 response. stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert lines[0].strip() == "Status: 500", (
        f"First stdout line for an HTTP 500 response must be 'Status: 500'; got: {lines[0]!r}"
    )
