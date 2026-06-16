import json
import os
import re
import shutil
import subprocess
import textwrap

import pytest

PROJECT_DIR = "/home/user/myproject"
CONFIG_PATH = os.path.join(PROJECT_DIR, "capacitor.config.ts")
CLIENT_PATH = os.path.join(PROJECT_DIR, "src", "api", "httpClient.ts")
HARNESS_DIR = "/tmp/httpclient-verify"
HARNESS_DIST = os.path.join(HARNESS_DIR, "dist")


# ---------------------------------------------------------------------------
# Static / file-content checks
# ---------------------------------------------------------------------------


def test_capacitor_config_enables_capacitor_http():
    assert os.path.isfile(CONFIG_PATH), (
        f"capacitor.config.ts not found at {CONFIG_PATH}."
    )
    with open(CONFIG_PATH) as f:
        content = f.read()

    # Core fields must remain.
    assert "com.example.myapp" in content, (
        "capacitor.config.ts should retain the original appId 'com.example.myapp'."
    )
    assert "My Native App" in content, (
        "capacitor.config.ts should retain the original appName 'My Native App'."
    )
    assert re.search(r"webDir\s*:\s*['\"]dist['\"]", content), (
        "capacitor.config.ts should retain webDir: 'dist'."
    )

    # CapacitorHttp must be enabled inside the plugins block.
    assert "CapacitorHttp" in content, (
        "capacitor.config.ts must reference the CapacitorHttp plugin."
    )
    # Tolerate both `enabled: true` and `"enabled": true`.
    plugins_pattern = re.compile(
        r"CapacitorHttp\s*:\s*{[^}]*enabled\s*:\s*true",
        re.DOTALL,
    )
    assert plugins_pattern.search(content), (
        "capacitor.config.ts must enable CapacitorHttp via "
        "plugins.CapacitorHttp.enabled = true."
    )


def test_http_client_file_exists():
    assert os.path.isfile(CLIENT_PATH), (
        f"Expected helper module at {CLIENT_PATH}."
    )


def test_http_client_uses_capacitor_http_request_and_preferences():
    with open(CLIENT_PATH) as f:
        src = f.read()
    assert "@capacitor/core" in src, (
        "httpClient.ts must import from '@capacitor/core'."
    )
    assert "@capacitor/preferences" in src, (
        "httpClient.ts must import Preferences from '@capacitor/preferences'."
    )
    assert "CapacitorHttp" in src and "request" in src, (
        "httpClient.ts must call CapacitorHttp.request."
    )
    assert "auth_token" in src, (
        "httpClient.ts must reference the 'auth_token' preferences key."
    )


def test_npm_build_succeeds():
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "`npm run build` must succeed (tsc --noEmit must report no errors). "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# Runtime behavior checks via Node + mock loader
# ---------------------------------------------------------------------------


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _setup_node_harness() -> None:
    if os.path.isdir(HARNESS_DIR):
        shutil.rmtree(HARNESS_DIR)
    os.makedirs(HARNESS_DIR, exist_ok=True)

    _write(
        os.path.join(HARNESS_DIR, "package.json"),
        json.dumps({"name": "httpclient-verify", "type": "module"}, indent=2),
    )

    _write(
        os.path.join(HARNESS_DIR, "state.mjs"),
        textwrap.dedent(
            """
            export const state = {
              mockResponse: null,
              recordedCalls: [],
              store: new Map(),
            };
            export function reset({ response, token }) {
              state.mockResponse = response;
              state.recordedCalls = [];
              state.store.clear();
              if (token !== undefined && token !== null) {
                state.store.set('auth_token', token);
              }
            }
            """
        ).strip()
        + "\n",
    )

    _write(
        os.path.join(HARNESS_DIR, "mocks", "capacitor-core.mjs"),
        textwrap.dedent(
            """
            import { state } from '../state.mjs';
            export const CapacitorHttp = {
              async request(options) {
                state.recordedCalls.push(JSON.parse(JSON.stringify({
                  url: options?.url,
                  method: options?.method,
                  headers: options?.headers ?? null,
                  params: options?.params ?? null,
                  data: options?.data,
                  hasData: Object.prototype.hasOwnProperty.call(options ?? {}, 'data'),
                })));
                return state.mockResponse;
              },
            };
            export default { CapacitorHttp };
            """
        ).strip()
        + "\n",
    )

    _write(
        os.path.join(HARNESS_DIR, "mocks", "capacitor-preferences.mjs"),
        textwrap.dedent(
            """
            import { state } from '../state.mjs';
            export const Preferences = {
              async get({ key }) {
                return { value: state.store.has(key) ? state.store.get(key) : null };
              },
              async set({ key, value }) {
                state.store.set(key, value);
              },
              async remove({ key }) {
                state.store.delete(key);
              },
              async clear() {
                state.store.clear();
              },
              async keys() {
                return { keys: Array.from(state.store.keys()) };
              },
            };
            export default { Preferences };
            """
        ).strip()
        + "\n",
    )

    _write(
        os.path.join(HARNESS_DIR, "loader.mjs"),
        textwrap.dedent(
            """
            import { fileURLToPath, pathToFileURL } from 'node:url';
            import { dirname, resolve as resolvePath } from 'node:path';

            const HERE = dirname(fileURLToPath(import.meta.url));
            const overrides = {
              '@capacitor/core': pathToFileURL(resolvePath(HERE, 'mocks/capacitor-core.mjs')).href,
              '@capacitor/preferences': pathToFileURL(resolvePath(HERE, 'mocks/capacitor-preferences.mjs')).href,
            };

            export async function resolve(specifier, context, nextResolve) {
              if (overrides[specifier]) {
                return { url: overrides[specifier], shortCircuit: true, format: 'module' };
              }
              return nextResolve(specifier, context);
            }
            """
        ).strip()
        + "\n",
    )

    _write(
        os.path.join(HARNESS_DIR, "register.mjs"),
        textwrap.dedent(
            """
            import { register } from 'node:module';
            import { pathToFileURL } from 'node:url';
            register('./loader.mjs', pathToFileURL(import.meta.url));
            """
        ).strip()
        + "\n",
    )

    _write(
        os.path.join(HARNESS_DIR, "run.mjs"),
        textwrap.dedent(
            """
            import assert from 'node:assert/strict';
            import { state, reset } from './state.mjs';

            const distUrl = new URL('./dist/httpClient.js', import.meta.url).href;
            const mod = await import(distUrl);

            const exported = Object.keys(mod);
            assert.ok(typeof mod.httpGet === 'function',
              'httpGet must be exported as a function. exports=' + JSON.stringify(exported));
            assert.ok(typeof mod.httpPost === 'function',
              'httpPost must be exported as a function. exports=' + JSON.stringify(exported));
            assert.ok(typeof mod.UnauthorizedError === 'function',
              'UnauthorizedError must be exported as a class. exports=' + JSON.stringify(exported));

            const { httpGet, httpPost, UnauthorizedError } = mod;
            const results = [];
            function record(name, ok, detail) {
              results.push({ name, ok, detail });
            }

            // ---- Scenario A: GET with token ----
            try {
              reset({
                response: { status: 200, data: { foo: 1 }, headers: { 'x-trace': 'a' }, url: 'https://api.example.com/items' },
                token: 'tok-abc',
              });
              const res = await httpGet('https://api.example.com/items', { page: '2' });
              assert.equal(res.status, 200, 'status should be 200');
              assert.deepEqual(res.data, { foo: 1 }, 'data should pass through');
              assert.deepEqual(res.headers, { 'x-trace': 'a' }, 'headers should pass through');
              assert.equal(state.recordedCalls.length, 1, 'one request expected');
              const call = state.recordedCalls[0];
              assert.equal(call.method, 'GET', 'method must be GET');
              assert.equal(call.url, 'https://api.example.com/items', 'url must match');
              assert.deepEqual(call.params, { page: '2' }, 'params must be forwarded');
              const authA = call.headers && (call.headers.Authorization ?? call.headers.authorization);
              assert.equal(authA, 'Bearer tok-abc', 'Authorization header must be Bearer tok-abc');
              const ctA = call.headers && (call.headers['Content-Type'] ?? call.headers['content-type']);
              assert.equal(ctA, undefined, 'Content-Type must not be set on GET');
              record('A_get_with_token', true, null);
            } catch (e) {
              record('A_get_with_token', false, String(e && e.stack || e));
            }

            // ---- Scenario B: GET without token ----
            try {
              reset({
                response: { status: 204, data: null, headers: {}, url: 'u' },
                token: null,
              });
              const res = await httpGet('https://api.example.com/health');
              assert.equal(res.status, 204, 'status should be 204');
              assert.equal(res.data, null, 'data should be null');
              const call = state.recordedCalls[0];
              const authB = call.headers && (call.headers.Authorization ?? call.headers.authorization);
              assert.equal(authB, undefined, 'Authorization must be absent when token is null');
              record('B_get_without_token', true, null);
            } catch (e) {
              record('B_get_without_token', false, String(e && e.stack || e));
            }

            // ---- Scenario C: POST with JSON body ----
            try {
              reset({
                response: { status: 201, data: { id: 7 }, headers: {}, url: 'u' },
                token: 'tok-xyz',
              });
              const res = await httpPost('https://api.example.com/items', { name: 'widget' });
              assert.equal(res.status, 201, 'status should be 201');
              assert.deepEqual(res.data, { id: 7 }, 'data should pass through');
              const call = state.recordedCalls[0];
              assert.equal(call.method, 'POST', 'method must be POST');
              const authC = call.headers && (call.headers.Authorization ?? call.headers.authorization);
              assert.equal(authC, 'Bearer tok-xyz', 'Authorization header must be Bearer tok-xyz');
              const ctC = call.headers && (call.headers['Content-Type'] ?? call.headers['content-type']);
              assert.equal(ctC, 'application/json', 'Content-Type must be application/json');
              assert.deepEqual(call.data, { name: 'widget' }, 'data field must equal the body');
              record('C_post_with_body', true, null);
            } catch (e) {
              record('C_post_with_body', false, String(e && e.stack || e));
            }

            // ---- Scenario D: POST with no body ----
            try {
              reset({
                response: { status: 200, data: {}, headers: {}, url: 'u' },
                token: 'tok-xyz',
              });
              await httpPost('https://api.example.com/ping');
              const call = state.recordedCalls[0];
              const ctD = call.headers && (call.headers['Content-Type'] ?? call.headers['content-type']);
              assert.equal(ctD, undefined, 'Content-Type must NOT be set when body is undefined');
              assert.equal(call.hasData === true && call.data !== undefined, false,
                'data should be unset (or undefined) when body is undefined');
              record('D_post_no_body', true, null);
            } catch (e) {
              record('D_post_no_body', false, String(e && e.stack || e));
            }

            // ---- Scenario E: 401 clears token & throws UnauthorizedError ----
            try {
              reset({
                response: { status: 401, data: { error: 'expired' }, headers: {}, url: 'u' },
                token: 'stale',
              });
              let caught = null;
              try {
                await httpGet('https://api.example.com/secret');
              } catch (err) {
                caught = err;
              }
              assert.ok(caught !== null, '401 must reject');
              assert.ok(caught instanceof UnauthorizedError,
                'rejection must be instance of UnauthorizedError, got ' + (caught && caught.constructor && caught.constructor.name));
              assert.equal(caught.status, 401, 'error.status must be 401');
              assert.equal(caught.url, 'https://api.example.com/secret', 'error.url must match request url');
              assert.equal(state.store.has('auth_token'), false,
                'auth_token must be removed from Preferences after a 401');
              record('E_401_clears_token', true, null);
            } catch (e) {
              record('E_401_clears_token', false, String(e && e.stack || e));
            }

            // ---- Scenario F: 500 preserves token & throws generic Error ----
            try {
              reset({
                response: { status: 500, data: { error: 'boom' }, headers: {}, url: 'u' },
                token: 'keep',
              });
              let caught = null;
              try {
                await httpPost('https://api.example.com/items', { x: 1 });
              } catch (err) {
                caught = err;
              }
              assert.ok(caught !== null, '500 must reject');
              assert.ok(!(caught instanceof UnauthorizedError),
                'non-401 errors must NOT be UnauthorizedError');
              assert.ok(/500/.test(String(caught && caught.message)),
                'error message must include the status code 500, got: ' + (caught && caught.message));
              assert.equal(state.store.get('auth_token'), 'keep',
                'auth_token must be preserved on non-401 errors');
              record('F_500_preserves_token', true, null);
            } catch (e) {
              record('F_500_preserves_token', false, String(e && e.stack || e));
            }

            console.log('SCENARIO_RESULTS=' + JSON.stringify(results));
            const failed = results.filter(r => !r.ok);
            if (failed.length > 0) {
              process.exit(1);
            }
            """
        ).strip()
        + "\n",
    )


def _compile_user_module() -> subprocess.CompletedProcess:
    os.makedirs(HARNESS_DIST, exist_ok=True)
    cmd = [
        "npx",
        "--no-install",
        "tsc",
        "--outDir",
        HARNESS_DIST,
        "--module",
        "nodenext",
        "--moduleResolution",
        "nodenext",
        "--target",
        "es2022",
        "--esModuleInterop",
        "--skipLibCheck",
        "--allowSyntheticDefaultImports",
        "--rootDir",
        os.path.join(PROJECT_DIR, "src"),
        os.path.join(PROJECT_DIR, "src", "api", "httpClient.ts"),
    ]
    return subprocess.run(
        cmd,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )


@pytest.fixture(scope="module")
def runtime_results():
    """Compile the user's module and run the Node harness once per session."""
    _setup_node_harness()

    compile_result = _compile_user_module()
    assert compile_result.returncode == 0, (
        "Failed to compile src/api/httpClient.ts for runtime verification. "
        f"stdout={compile_result.stdout!r} stderr={compile_result.stderr!r}"
    )

    compiled_path = os.path.join(HARNESS_DIST, "api", "httpClient.js")
    if not os.path.isfile(compiled_path):
        # Fallback: tsc may have placed the file at dist/httpClient.js depending on rootDir.
        alt = os.path.join(HARNESS_DIST, "httpClient.js")
        if os.path.isfile(alt):
            os.makedirs(os.path.join(HARNESS_DIST, "api"), exist_ok=True)
            shutil.copy(alt, compiled_path)
    # Link/copy the compiled file to dist/httpClient.js so run.mjs can import it deterministically.
    target = os.path.join(HARNESS_DIST, "httpClient.js")
    if os.path.isfile(compiled_path) and not os.path.isfile(target):
        shutil.copy(compiled_path, target)
    assert os.path.isfile(target), (
        f"Compiled module not found at {target}. "
        f"Listing of {HARNESS_DIST}: {os.listdir(HARNESS_DIST) if os.path.isdir(HARNESS_DIST) else 'missing'}"
    )

    # Provide a local node_modules so @capacitor/* resolution would normally work,
    # but the loader intercepts these specifiers before module resolution runs.
    run_result = subprocess.run(
        ["node", "--import", "./register.mjs", "./run.mjs"],
        cwd=HARNESS_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )

    results = []
    for line in (run_result.stdout or "").splitlines():
        if line.startswith("SCENARIO_RESULTS="):
            try:
                results = json.loads(line[len("SCENARIO_RESULTS=") :])
            except json.JSONDecodeError:
                results = []

    return {
        "returncode": run_result.returncode,
        "stdout": run_result.stdout,
        "stderr": run_result.stderr,
        "results": results,
    }


def _result_for(results, name):
    for entry in results:
        if entry.get("name") == name:
            return entry
    return None


def test_runtime_harness_runs(runtime_results):
    assert runtime_results["results"], (
        "No scenario results were captured from the Node harness. "
        f"stdout={runtime_results['stdout']!r} stderr={runtime_results['stderr']!r}"
    )


def test_scenario_A_get_with_token(runtime_results):
    entry = _result_for(runtime_results["results"], "A_get_with_token")
    assert entry is not None and entry.get("ok"), (
        "Scenario A failed (GET attaches Bearer token, no Content-Type, forwards params). "
        f"detail={entry and entry.get('detail')}"
    )


def test_scenario_B_get_without_token(runtime_results):
    entry = _result_for(runtime_results["results"], "B_get_without_token")
    assert entry is not None and entry.get("ok"), (
        "Scenario B failed (GET without stored token must omit Authorization header). "
        f"detail={entry and entry.get('detail')}"
    )


def test_scenario_C_post_with_body(runtime_results):
    entry = _result_for(runtime_results["results"], "C_post_with_body")
    assert entry is not None and entry.get("ok"), (
        "Scenario C failed (POST must send JSON body, Content-Type header, and Bearer token). "
        f"detail={entry and entry.get('detail')}"
    )


def test_scenario_D_post_no_body(runtime_results):
    entry = _result_for(runtime_results["results"], "D_post_no_body")
    assert entry is not None and entry.get("ok"), (
        "Scenario D failed (POST without body must omit data and Content-Type). "
        f"detail={entry and entry.get('detail')}"
    )


def test_scenario_E_401_clears_token(runtime_results):
    entry = _result_for(runtime_results["results"], "E_401_clears_token")
    assert entry is not None and entry.get("ok"), (
        "Scenario E failed (401 must clear auth_token and throw UnauthorizedError). "
        f"detail={entry and entry.get('detail')}"
    )


def test_scenario_F_500_preserves_token(runtime_results):
    entry = _result_for(runtime_results["results"], "F_500_preserves_token")
    assert entry is not None and entry.get("ok"), (
        "Scenario F failed (500 must throw a non-UnauthorizedError and preserve the token). "
        f"detail={entry and entry.get('detail')}"
    )
