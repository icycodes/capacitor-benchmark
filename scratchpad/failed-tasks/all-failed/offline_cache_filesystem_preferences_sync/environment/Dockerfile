FROM ubuntu:24.04

# ---------------------------------------------------------------------------
# Base system packages + Node.js 24 (satisfies Capacitor v8's Node 22+ minimum).
# Browser system libraries are installed so that Playwright's bundled
# Chromium can launch headless during final-state verification.
# ---------------------------------------------------------------------------
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep \
        ffmpeg libxcb-shm0 libx11-xcb1 libx11-6 libxcb1 libxext6 libxrandr2 \
        libxcomposite1 libxcursor1 libxdamage1 libxfixes3 libxi6 libgtk-3-0t64 \
        libpangocairo-1.0-0 libpango-1.0-0 libatk1.0-0t64 libcairo-gobject2 libcairo2 \
        libgdk-pixbuf-2.0-0 libxrender1 libasound2t64 libfreetype6 libfontconfig1 \
        libdbus-1-3 libnss3 libnspr4 libatk-bridge2.0-0t64 libdrm2 libxkbcommon0 \
        libatspi2.0-0t64 libcups2t64 libxshmfence1 libgbm1 && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    pip3 install --break-system-packages \
        pytest-json-ctrf \
        pytest-xprocess \
        requests \
        playwright && \
    python3 -m playwright install chromium && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

# ---------------------------------------------------------------------------
# Pre-scaffold a minimal Vite + TypeScript project at /home/user/myapp.
# The executor will integrate Capacitor v8 + the @capacitor/filesystem and
# @capacitor/preferences plugins on top of this base project and implement
# src/cache/offlineCache.ts using CapacitorHttp.
# ---------------------------------------------------------------------------
RUN mkdir -p /home/user/myapp/src && \
    cat >/home/user/myapp/package.json <<'EOF'
{
  "name": "myapp",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "typescript": "~5.4.5",
    "vite": "~5.4.10"
  }
}
EOF

RUN cat >/home/user/myapp/index.html <<'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Offline Cache Demo</title>
  </head>
  <body>
    <main id="app">
      <h1>Offline Cache Demo</h1>
    </main>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
EOF

RUN cat >/home/user/myapp/src/main.ts <<'EOF'
// Initial scaffold. The executor must replace this with an implementation
// that wires the Offline Cache UI to src/cache/offlineCache.ts.
const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Replace me with the Offline Cache UI wiring.";
  app.appendChild(note);
}
EOF

RUN cat >/home/user/myapp/tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": false,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "noEmit": true,
    "strict": true
  },
  "include": ["src", "vite.config.ts"]
}
EOF

# Install Vite dependencies up front so the offline-friendly task environment
# matches the assumptions in test_initial_state.py (node_modules pre-populated).
RUN cd /home/user/myapp && npm install --no-audit --no-fund

# ---------------------------------------------------------------------------
# Bundle a small ETag-aware fixture HTTP server at /opt/fixtures/etag_server.js.
# The verifier starts it on port 4174 before driving the browser-based checks.
# It supports:
#   - GET  /api/data           Returns the current JSON body (200) with `ETag`
#                              and permissive CORS headers. If the request
#                              carries an `If-None-Match` header matching the
#                              current ETag, returns 304 with an empty body.
#   - GET  /api/control/stats  Returns request stats and the current ETag/body.
#   - POST /api/control/reset  Resets traffic counters and lastIfNoneMatch.
#   - POST /api/control/rotate Replaces the body and ETag with a new pair.
#                              Returns { etag, body }.
# ---------------------------------------------------------------------------
RUN mkdir -p /opt/fixtures && \
    cat >/opt/fixtures/etag_server.js <<'EOF'
"use strict";

const http = require("http");
const { URL } = require("url");

function parseArgs(argv) {
  const out = { port: 4174 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--port" && argv[i + 1]) {
      out.port = parseInt(argv[++i], 10);
    }
  }
  return out;
}

const args = parseArgs(process.argv.slice(2));

// In-memory state.
let payloadVersion = 1;
function buildPayload(version) {
  return {
    etag: `W/"v${version}"`,
    body: {
      version,
      message: `payload version ${version}`,
      items: Array.from({ length: 3 }, (_, i) => ({
        id: i + 1,
        label: `item-${version}-${i + 1}`,
      })),
    },
  };
}
let current = buildPayload(payloadVersion);

const stats = {
  total: 0,
  last200: 0,
  last304: 0,
  lastIfNoneMatch: null,
  lastEtag: null,
};

function setCors(res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "If-None-Match, Content-Type");
  res.setHeader("Access-Control-Expose-Headers", "ETag");
}

function findHeader(req, name) {
  const lower = name.toLowerCase();
  for (const k of Object.keys(req.headers)) {
    if (k.toLowerCase() === lower) {
      return req.headers[k];
    }
  }
  return undefined;
}

function sendJson(res, status, payload) {
  setCors(res);
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify(payload));
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url || "/", `http://${req.headers.host || "127.0.0.1"}`);

  if (req.method === "OPTIONS") {
    setCors(res);
    res.statusCode = 204;
    res.end();
    return;
  }

  if (url.pathname === "/api/data" && req.method === "GET") {
    const ifNoneMatch = findHeader(req, "if-none-match");
    stats.total += 1;
    stats.lastIfNoneMatch = ifNoneMatch === undefined ? null : ifNoneMatch;
    stats.lastEtag = current.etag;
    setCors(res);
    res.setHeader("ETag", current.etag);
    if (ifNoneMatch && ifNoneMatch === current.etag) {
      stats.last304 += 1;
      res.statusCode = 304;
      res.end();
      return;
    }
    stats.last200 += 1;
    res.statusCode = 200;
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify(current.body));
    return;
  }

  if (url.pathname === "/api/control/stats" && req.method === "GET") {
    sendJson(res, 200, {
      total: stats.total,
      last200: stats.last200,
      last304: stats.last304,
      lastIfNoneMatch: stats.lastIfNoneMatch,
      lastEtag: stats.lastEtag,
      currentEtag: current.etag,
      currentBody: current.body,
    });
    return;
  }

  if (url.pathname === "/api/control/reset" && req.method === "POST") {
    stats.total = 0;
    stats.last200 = 0;
    stats.last304 = 0;
    stats.lastIfNoneMatch = null;
    stats.lastEtag = null;
    sendJson(res, 200, { ok: true });
    return;
  }

  if (url.pathname === "/api/control/rotate" && req.method === "POST") {
    payloadVersion += 1;
    current = buildPayload(payloadVersion);
    sendJson(res, 200, { etag: current.etag, body: current.body });
    return;
  }

  setCors(res);
  res.statusCode = 404;
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify({ error: "Not Found", path: url.pathname }));
});

server.listen(args.port, "0.0.0.0", () => {
  // eslint-disable-next-line no-console
  console.log(`etag_server listening on http://127.0.0.1:${args.port}`);
});

function shutdown() {
  server.close(() => process.exit(0));
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
EOF

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 task environment: pre-scaffolded Vite + TypeScript project at /home/user/myapp, plus a Node.js ETag-aware fixture HTTP server at /opt/fixtures/etag_server.js for offline-cache verification."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 (satisfies Capacitor v8 Node 22+ requirement)
#   - pip3 packages for verification: pytest-xprocess, requests, playwright (+ chromium browser)
#   - Browser system libraries for headless Chromium (Playwright)
#   - /home/user/myapp: pre-scaffolded Vite + TypeScript project with node_modules installed
#   - /opt/fixtures/etag_server.js: ETag-aware JSON fixture server used by the verifier
