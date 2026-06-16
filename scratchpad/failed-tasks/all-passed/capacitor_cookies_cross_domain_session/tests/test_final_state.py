import os
import re
import subprocess

import pytest

PROJECT_DIR = "/home/user/myproject"
VERIFIER_DIR = "/home/user/verifier"
CONFIG_PATH = os.path.join(PROJECT_DIR, "capacitor.config.ts")
SESSION_PATH = os.path.join(PROJECT_DIR, "src", "auth", "session.ts")
RUN_SCRIPT = os.path.join(PROJECT_DIR, "run_session_check.sh")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_capacitor_config_enables_cookies():
    assert os.path.isfile(CONFIG_PATH), f"Missing {CONFIG_PATH}."
    content = _read(CONFIG_PATH)
    # Tolerant of whitespace/quoting variants.
    normalized = re.sub(r"\s+", "", content)
    # Match either CapacitorCookies:{...enabled:true...} or "CapacitorCookies":{...enabled:true...}
    pattern = re.compile(
        r"""["']?CapacitorCookies["']?:\{[^}]*enabled:true""",
        re.DOTALL,
    )
    assert pattern.search(normalized), (
        "capacitor.config.ts must enable CapacitorCookies with `enabled: true` "
        "inside the `plugins` object. Got:\n" + content
    )


def test_session_module_exists():
    assert os.path.isfile(SESSION_PATH), (
        f"Expected TypeScript session module at {SESSION_PATH}."
    )


def test_session_imports_capacitor_apis():
    content = _read(SESSION_PATH)
    assert "@capacitor/core" in content, (
        "src/auth/session.ts must import from '@capacitor/core'."
    )
    assert re.search(r"CapacitorCookies", content), (
        "src/auth/session.ts must reference CapacitorCookies."
    )
    assert re.search(r"CapacitorHttp", content), (
        "src/auth/session.ts must reference CapacitorHttp."
    )


def test_session_exposes_required_async_functions():
    content = _read(SESSION_PATH)
    # Allow either `export async function name(` or `export const name = async (`.
    patterns = {
        "login": [
            r"export\s+async\s+function\s+login\s*\(",
            r"export\s+const\s+login\s*=\s*async\s*\(",
            r"export\s+const\s+login\s*:\s*[^=]+=\s*async\s*\(",
        ],
        "whoami": [
            r"export\s+async\s+function\s+whoami\s*\(",
            r"export\s+const\s+whoami\s*=\s*async\s*\(",
            r"export\s+const\s+whoami\s*:\s*[^=]+=\s*async\s*\(",
        ],
        "logout": [
            r"export\s+async\s+function\s+logout\s*\(",
            r"export\s+const\s+logout\s*=\s*async\s*\(",
            r"export\s+const\s+logout\s*:\s*[^=]+=\s*async\s*\(",
        ],
    }
    for name, alt in patterns.items():
        assert any(re.search(p, content) for p in alt), (
            f"src/auth/session.ts must export an async function named '{name}'."
        )


def test_session_references_session_id_and_clear_all_cookies():
    content = _read(SESSION_PATH)
    assert "session_id" in content, (
        "src/auth/session.ts must reference the 'session_id' cookie key."
    )
    assert "clearAllCookies" in content, (
        "src/auth/session.ts must call CapacitorCookies.clearAllCookies (logout)."
    )
    assert "API_BASE_URL" in content, (
        "src/auth/session.ts must read its base URL from API_BASE_URL."
    )


def test_typescript_typecheck_succeeds():
    result = subprocess.run(
        ["npx", "tsc", "--noEmit"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "TypeScript type-check (`npx tsc --noEmit`) must succeed.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


@pytest.fixture(scope="module")
def install_run_script():
    """Copy the verifier's run_session_check.sh into the project so users can rerun it."""
    src = os.path.join(VERIFIER_DIR, "run_session_check.sh")
    assert os.path.isfile(src), f"Missing verifier script {src}."
    with open(src, encoding="utf-8") as f:
        content = f.read()
    with open(RUN_SCRIPT, "w", encoding="utf-8") as f:
        f.write(content)
    os.chmod(RUN_SCRIPT, 0o755)
    yield RUN_SCRIPT


def test_behavioral_run_passes(install_run_script):
    result = subprocess.run(
        ["bash", install_run_script],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    combined = result.stdout + "\n" + result.stderr
    assert result.returncode == 0, (
        "Behavioral verifier script failed with non-zero exit.\n" + combined
    )
    assert "RESULT: PASS" in result.stdout, (
        "Behavioral verifier script must print 'RESULT: PASS' to stdout.\n" + combined
    )
