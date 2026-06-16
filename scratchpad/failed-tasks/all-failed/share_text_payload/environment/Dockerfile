FROM ubuntu:24.04

# ---------------------------------------------------------------------------
# Base system packages + Node.js 24 (satisfies Capacitor v8's Node 22+ minimum)
# plus the runtime libraries required by Playwright Chromium. The final-state
# verifier drives a real headless Chromium via the Playwright Python SDK to
# intercept navigator.share and assert the Share.share payload after a click.
# ---------------------------------------------------------------------------
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep \
        ffmpeg libxcb-shm0 libx11-xcb1 libx11-6 libxcb1 libxext6 libxrandr2 \
        libxcomposite1 libxcursor1 libxdamage1 libxfixes3 libxi6 libgtk-3-0t64 \
        libpangocairo-1.0-0 libpango-1.0-0 libatk1.0-0t64 libcairo-gobject2 \
        libcairo2 libgdk-pixbuf-2.0-0 libxrender1 libasound2t64 libfreetype6 \
        libfontconfig1 libdbus-1-3 libnss3 libnspr4 libatk-bridge2.0-0t64 \
        libdrm2 libxkbcommon0 libatspi2.0-0t64 libcups2t64 libxshmfence1 libgbm1 && \
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
# Pre-scaffold a Vite + TypeScript project with Capacitor v8 already installed
# and initialised at /home/user/myapp. The executor must add the
# @capacitor/share v8 plugin, render a <button id="share-btn"> on the page,
# and wire its click handler to call Share.share with the expected payload.
# ---------------------------------------------------------------------------
RUN mkdir -p /home/user/myapp/src

RUN cat >/home/user/myapp/package.json <<'EOF'
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
  "dependencies": {
    "@capacitor/core": "^8.0.0"
  },
  "devDependencies": {
    "@capacitor/cli": "^8.0.0",
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
    <title>Share Payload Demo</title>
  </head>
  <body>
    <main id="app">
      <h1>Share Payload Demo</h1>
      <p>Install @capacitor/share and wire up the share button here.</p>
    </main>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
EOF

RUN cat >/home/user/myapp/src/main.ts <<'EOF'
// Initial scaffold. The executor must install @capacitor/share v8, render a
// <button id="share-btn"> on the page (here or in index.html), and call
// Share.share({ title: "Demo", text: "Hello from Capacitor", dialogTitle: "Choose" })
// on click.
const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Replace me with a Share integration.";
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

# Pre-existing Capacitor v8 configuration without any Share wiring.
RUN cat >/home/user/myapp/capacitor.config.ts <<'EOF'
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.myapp',
  appName: 'Share Payload Demo',
  webDir: 'dist',
};

export default config;
EOF

# Install all core dependencies up front so the executor only has to add
# @capacitor/share at v8. The initial-state tests check that the plugin is
# absent both from package.json and from node_modules.
RUN cd /home/user/myapp && npm install --no-audit --no-fund

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 task environment: pre-scaffolded Vite + TypeScript project with Capacitor core/CLI installed and Playwright Chromium for share-payload verification; @capacitor/share NOT yet installed."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 (satisfies Capacitor v8 Node 22+ requirement)
#   - Playwright + Chromium browser dependencies installed for headless verification
#   - pip3 packages for verification: pytest-xprocess, requests, playwright
#   - /home/user/myapp: pre-scaffolded Vite + TypeScript + Capacitor v8 project
#       * @capacitor/core and @capacitor/cli installed in node_modules
#       * capacitor.config.ts present (no Share wiring yet)
#       * @capacitor/share NOT installed
#       * src/main.ts scaffold without Share calls or share button
