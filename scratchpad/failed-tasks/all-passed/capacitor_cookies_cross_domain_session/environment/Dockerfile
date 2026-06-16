FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends nodejs && \
    pip3 install --break-system-packages pytest-json-ctrf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

# ----- Capacitor v8 project scaffold -----
RUN mkdir -p /home/user/myproject/src && \
    cd /home/user/myproject && \
    cat >package.json <<'JSON'
{
  "name": "capacitor-cookies-session-task",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "typecheck": "tsc --noEmit"
  }
}
JSON

RUN cat >/home/user/myproject/capacitor.config.ts <<'TS'
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.cookiesession',
  appName: 'CookieSession',
  webDir: 'dist',
};

export default config;
TS

RUN cat >/home/user/myproject/tsconfig.json <<'JSON'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "types": ["node"]
  },
  "include": ["src/**/*.ts", "capacitor.config.ts"]
}
JSON

RUN cd /home/user/myproject && \
    npm install --no-fund --no-audit --loglevel=error \
        @capacitor/core@^8.0.0 \
        @capacitor/cli@^8.0.0 \
        typescript@^5.5.0 \
        @types/node@^22.0.0

# ----- Verifier harness -----
RUN mkdir -p /home/user/verifier && \
    cat >/home/user/verifier/package.json <<'JSON'
{
  "name": "capacitor-cookies-session-verifier",
  "version": "1.0.0",
  "private": true,
  "type": "module"
}
JSON

RUN cat >/home/user/verifier/capacitor-loader.mjs <<'MJS'
// Resolver hook that maps `@capacitor/core` to our in-process shim.
const SHIM_URL = new URL('./capacitor-core-shim.mjs', import.meta.url).href;

export async function resolve(specifier, context, nextResolve) {
  if (specifier === '@capacitor/core') {
    return { url: SHIM_URL, shortCircuit: true, format: 'module' };
  }
  return nextResolve(specifier, context);
}
MJS

RUN cat >/home/user/verifier/capacitor-core-shim.mjs <<'MJS'
// Lightweight, in-process replacement for `@capacitor/core` that:
//   * records every CapacitorCookies call (so the verifier can assert behavior),
//   * keeps a real in-memory cookie jar keyed by request origin,
//   * routes CapacitorHttp through Node's native `http` module so requests go to a
//     real fixture server (no mocking of the candidate's code).
import http from 'node:http';

const cookieJar = new Map();                // key: `${origin}|${name}` -> value
const setCookieLog = [];                    // every CapacitorCookies.setCookie call
const clearAllCookiesLog = [];              // every CapacitorCookies.clearAllCookies call
const httpLog = [];                         // every CapacitorHttp request

export const __log = {
  cookieJar,
  setCookieLog,
  clearAllCookiesLog,
  httpLog,
  reset() {
    cookieJar.clear();
    setCookieLog.length = 0;
    clearAllCookiesLog.length = 0;
    httpLog.length = 0;
  },
};

function originOf(u) {
  try {
    return new URL(u).origin;
  } catch {
    return '';
  }
}

export const CapacitorCookies = {
  async setCookie(opts) {
    const { url, key, value } = opts || {};
    setCookieLog.push({ url, key, value });
    const origin = originOf(url);
    if (origin && key) {
      cookieJar.set(`${origin}|${key}`, String(value ?? ''));
    }
  },
  async getCookies(opts = {}) {
    const origin = originOf(opts.url || '');
    const out = {};
    for (const [k, v] of cookieJar.entries()) {
      const [coOrigin, coKey] = k.split('|');
      if (!origin || coOrigin === origin) out[coKey] = v;
    }
    return out;
  },
  async deleteCookie({ url, key }) {
    const origin = originOf(url);
    cookieJar.delete(`${origin}|${key}`);
  },
  async clearCookies({ url }) {
    const origin = originOf(url);
    for (const k of [...cookieJar.keys()]) {
      if (k.startsWith(`${origin}|`)) cookieJar.delete(k);
    }
  },
  async clearAllCookies() {
    clearAllCookiesLog.push({ at: Date.now() });
    cookieJar.clear();
  },
};

function cookieHeaderFor(origin) {
  const parts = [];
  for (const [k, v] of cookieJar.entries()) {
    const [coOrigin, coKey] = k.split('|');
    if (coOrigin === origin) parts.push(`${coKey}=${v}`);
  }
  return parts.length ? parts.join('; ') : '';
}

function applySetCookieHeader(origin, setCookieHeader) {
  if (!setCookieHeader) return;
  const items = Array.isArray(setCookieHeader) ? setCookieHeader : [setCookieHeader];
  for (const raw of items) {
    if (typeof raw !== 'string') continue;
    const first = raw.split(';')[0];
    const eq = first.indexOf('=');
    if (eq <= 0) continue;
    const name = first.slice(0, eq).trim();
    const value = first.slice(eq + 1).trim();
    cookieJar.set(`${origin}|${name}`, value);
  }
}

function nativeRequest(urlString, method, headers, dataBody) {
  return new Promise((resolve, reject) => {
    let parsed;
    try {
      parsed = new URL(urlString);
    } catch (e) {
      reject(e);
      return;
    }
    const origin = parsed.origin;
    const reqHeaders = { ...(headers || {}) };
    const cookieHeader = cookieHeaderFor(origin);
    if (cookieHeader && !reqHeaders.Cookie && !reqHeaders.cookie) {
      reqHeaders.Cookie = cookieHeader;
    }

    let payload;
    if (dataBody !== undefined && dataBody !== null && method !== 'GET' && method !== 'HEAD') {
      if (typeof dataBody === 'string') {
        payload = dataBody;
      } else {
        payload = JSON.stringify(dataBody);
        if (!reqHeaders['Content-Type'] && !reqHeaders['content-type']) {
          reqHeaders['Content-Type'] = 'application/json';
        }
      }
    }

    const req = http.request({
      method,
      hostname: parsed.hostname,
      port: parsed.port || 80,
      path: parsed.pathname + parsed.search,
      headers: reqHeaders,
    }, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        const buf = Buffer.concat(chunks).toString('utf-8');
        applySetCookieHeader(origin, res.headers['set-cookie']);
        const ct = (res.headers['content-type'] || '').toLowerCase();
        let parsedBody = buf;
        if (ct.includes('json')) {
          try { parsedBody = JSON.parse(buf); } catch { /* fall back to raw */ }
        }
        const response = {
          status: res.statusCode || 0,
          data: parsedBody,
          headers: res.headers,
          url: urlString,
        };
        httpLog.push({ url: urlString, method, status: response.status });
        resolve(response);
      });
    });
    req.on('error', reject);
    if (payload !== undefined) req.write(payload);
    req.end();
  });
}

async function doRequest(opts) {
  const method = (opts.method || 'GET').toUpperCase();
  return nativeRequest(opts.url, method, opts.headers, opts.data);
}

export const CapacitorHttp = {
  request: (opts) => doRequest(opts),
  get: (opts) => doRequest({ ...opts, method: 'GET' }),
  post: (opts) => doRequest({ ...opts, method: 'POST' }),
  put: (opts) => doRequest({ ...opts, method: 'PUT' }),
  patch: (opts) => doRequest({ ...opts, method: 'PATCH' }),
  delete: (opts) => doRequest({ ...opts, method: 'DELETE' }),
};

export const registerPlugin = () => {
  throw new Error('registerPlugin is not used by this task; not implemented in shim.');
};

export default { CapacitorCookies, CapacitorHttp, registerPlugin };
MJS

RUN cat >/home/user/verifier/server.mjs <<'MJS'
// Tiny fixture HTTP server used by the behavioral verifier.
// Routes:
//   POST /login   -> 200 with {session_id, user} and Set-Cookie on success; 401 otherwise.
//   GET  /whoami  -> 200 with {user:'alice'} if cookie session_id=SESSION_TOKEN present; 401 otherwise.
import http from 'node:http';

export function startFixtureServer() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const chunks = [];
      req.on('data', (c) => chunks.push(c));
      req.on('end', () => {
        const body = Buffer.concat(chunks).toString('utf-8');
        const url = req.url || '/';
        if (req.method === 'POST' && url === '/login') {
          let payload = {};
          try { payload = JSON.parse(body || '{}'); } catch { payload = {}; }
          if (payload && payload.user === 'alice' && payload.pass === 'wonderland') {
            res.statusCode = 200;
            res.setHeader('Content-Type', 'application/json');
            res.setHeader('Set-Cookie', 'session_id=SESSION_TOKEN; Path=/');
            res.end(JSON.stringify({ session_id: 'SESSION_TOKEN', user: 'alice' }));
            return;
          }
          res.statusCode = 401;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: 'bad credentials' }));
          return;
        }
        if (req.method === 'GET' && url === '/whoami') {
          const cookie = req.headers.cookie || '';
          if (cookie.split(';').map((s) => s.trim()).some((c) => c === 'session_id=SESSION_TOKEN')) {
            res.statusCode = 200;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({ user: 'alice' }));
            return;
          }
          res.statusCode = 401;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: 'unauthenticated' }));
          return;
        }
        res.statusCode = 404;
        res.end();
      });
    });
    server.listen(0, '127.0.0.1', () => {
      const addr = server.address();
      const port = typeof addr === 'object' && addr ? addr.port : 0;
      resolve({ server, port });
    });
  });
}

if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  startFixtureServer().then(({ port }) => {
    console.log(`fixture listening on 127.0.0.1:${port}`);
  });
}
MJS

RUN cat >/home/user/verifier/verify_session.mjs <<'MJS'
// End-to-end behavioral verifier for src/auth/session.ts.
// Flow:
//   1. Register an ESM resolver hook that redirects `@capacitor/core` to our shim.
//   2. Start a real local fixture HTTP server.
//   3. Set process.env.API_BASE_URL so the candidate module reads our origin.
//   4. Dynamically import the compiled session module and run the four assertions.
import { register } from 'node:module';
register('./capacitor-loader.mjs', import.meta.url);

const SHIM_URL = new URL('./capacitor-core-shim.mjs', import.meta.url).href;
const shim = await import(SHIM_URL);
const { __log } = shim;

const { startFixtureServer } = await import('./server.mjs');

const failures = [];
function fail(msg) { failures.push(msg); }

const COMPILED_SESSION = process.env.COMPILED_SESSION_PATH || '/tmp/verify-build/auth/session.js';
const { server, port } = await startFixtureServer();
process.env.API_BASE_URL = `http://127.0.0.1:${port}`;

try {
  let sessionMod;
  try {
    sessionMod = await import(`file://${COMPILED_SESSION}?t=${Date.now()}`);
  } catch (e) {
    fail(`Could not import compiled session module at ${COMPILED_SESSION}: ${e && e.stack ? e.stack : e}`);
    sessionMod = {};
  }
  const { login, whoami, logout } = sessionMod;

  if (typeof login !== 'function') fail(`Expected 'login' to be an exported function; got ${typeof login}.`);
  if (typeof whoami !== 'function') fail(`Expected 'whoami' to be an exported function; got ${typeof whoami}.`);
  if (typeof logout !== 'function') fail(`Expected 'logout' to be an exported function; got ${typeof logout}.`);

  if (typeof login === 'function' && typeof whoami === 'function' && typeof logout === 'function') {
    // --- Case A: positive login ---
    __log.reset();
    let loginOk;
    try { loginOk = await login('alice', 'wonderland'); }
    catch (e) { fail(`Case A: login('alice','wonderland') threw: ${e && e.stack ? e.stack : e}`); }
    if (loginOk !== true) fail(`Case A: expected login to return boolean true; got ${JSON.stringify(loginOk)}.`);
    const okCookie = __log.setCookieLog.find((e) => e && e.key === 'session_id' && e.value === 'SESSION_TOKEN');
    if (!okCookie) fail(`Case A: expected CapacitorCookies.setCookie call with key='session_id', value='SESSION_TOKEN'. setCookieLog=${JSON.stringify(__log.setCookieLog)}`);

    // --- Case B: whoami after login ---
    let who;
    try { who = await whoami(); }
    catch (e) { fail(`Case B: whoami() threw: ${e && e.stack ? e.stack : e}`); }
    if (who !== 'alice') fail(`Case B: expected whoami() to return 'alice'; got ${JSON.stringify(who)}.`);

    // --- Case C: negative login (no prior session in jar) ---
    __log.reset();
    let loginBad;
    try { loginBad = await login('alice', 'bad'); }
    catch (e) { fail(`Case C: login('alice','bad') threw: ${e && e.stack ? e.stack : e}`); }
    if (loginBad !== false) fail(`Case C: expected login('alice','bad') to return boolean false; got ${JSON.stringify(loginBad)}.`);

    // --- Case D: logout calls clearAllCookies ---
    __log.reset();
    try { await logout(); }
    catch (e) { fail(`Case D: logout() threw: ${e && e.stack ? e.stack : e}`); }
    if (__log.clearAllCookiesLog.length < 1) fail(`Case D: expected logout() to invoke CapacitorCookies.clearAllCookies at least once. clearAllCookiesLog is empty.`);
  }
} catch (e) {
  fail(`Verifier threw: ${e && e.stack ? e.stack : e}`);
} finally {
  try { server.close(); } catch {}
}

if (failures.length === 0) {
  console.log('RESULT: PASS');
  process.exit(0);
} else {
  for (const f of failures) console.error('FAILURE:', f);
  console.log('RESULT: FAIL');
  process.exit(1);
}
MJS

RUN cat >/home/user/verifier/run_session_check.sh <<'SH'
#!/usr/bin/env bash
# End-to-end check: type-check the project, compile session.ts to ESM, run the
# behavioral verifier against a real local HTTP fixture server.
PROJECT_DIR="${PROJECT_DIR:-/home/user/myproject}"
VERIFIER_DIR="${VERIFIER_DIR:-/home/user/verifier}"
BUILD_DIR="${BUILD_DIR:-/tmp/verify-build}"

cd "$PROJECT_DIR" || { echo "FAILURE: cannot cd to $PROJECT_DIR"; echo "RESULT: FAIL"; exit 1; }

echo "[run_session_check] step 1/3: npx tsc --noEmit"
npx --no-install tsc --noEmit
TSC_NOEMIT_EXIT=$?
if [ $TSC_NOEMIT_EXIT -ne 0 ]; then
  echo "FAILURE: tsc --noEmit returned $TSC_NOEMIT_EXIT"
  echo "RESULT: FAIL"
  exit 1
fi

echo "[run_session_check] step 2/3: compile src/auth/session.ts"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
printf '{"type":"module"}\n' > "$BUILD_DIR/package.json"
npx --no-install tsc \
  --outDir "$BUILD_DIR" \
  --module esnext \
  --target es2022 \
  --moduleResolution node \
  --rootDir "$PROJECT_DIR/src" \
  --esModuleInterop \
  --strict \
  --skipLibCheck \
  --noEmit false \
  "$PROJECT_DIR/src/auth/session.ts"
TSC_BUILD_EXIT=$?
if [ $TSC_BUILD_EXIT -ne 0 ]; then
  echo "FAILURE: tsc compile of session.ts returned $TSC_BUILD_EXIT"
  echo "RESULT: FAIL"
  exit 1
fi
if [ ! -f "$BUILD_DIR/auth/session.js" ]; then
  echo "FAILURE: expected compiled output at $BUILD_DIR/auth/session.js"
  echo "RESULT: FAIL"
  exit 1
fi

echo "[run_session_check] step 3/3: behavioral verifier"
COMPILED_SESSION_PATH="$BUILD_DIR/auth/session.js" \
  node "$VERIFIER_DIR/verify_session.mjs"
exit $?
SH

RUN chmod +x /home/user/verifier/run_session_check.sh

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 starter project + verifier harness for the CapacitorCookies cross-domain session task."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v22 (Capacitor v8 requires Node 22+)
#   - /home/user/myproject: Capacitor v8 starter project (package.json, capacitor.config.ts without CapacitorCookies,
#     tsconfig.json, src/) with @capacitor/core@^8, @capacitor/cli@^8, typescript, @types/node installed.
#   - /home/user/verifier: harness containing
#       capacitor-loader.mjs (ESM resolver that redirects @capacitor/core to the shim),
#       capacitor-core-shim.mjs (in-process CapacitorCookies/CapacitorHttp backed by Node http + cookie jar),
#       server.mjs (fixture HTTP server with /login and /whoami),
#       verify_session.mjs (behavioral runner that asserts the 4 cases),
#       run_session_check.sh (end-to-end orchestrator emitting `RESULT: PASS`).
