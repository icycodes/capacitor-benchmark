FROM ubuntu:24.04

# ---------------------------------------------------------------------------
# Base system packages + Node.js 24 (satisfies Capacitor v8's Node 22+ minimum).
# This task does NOT need a real browser (the Status Bar plugin is a web no-op);
# we verify wiring through static checks plus a Vite preview HTTP fetch.
# ---------------------------------------------------------------------------
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    pip3 install --break-system-packages \
        pytest-json-ctrf \
        pytest-xprocess \
        requests && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

# ---------------------------------------------------------------------------
# Pre-scaffold a Vite + TypeScript project with Capacitor v8 already installed
# and initialised at /home/user/myapp. The executor must add the
# @capacitor/status-bar v8 plugin and wire StatusBar.setStyle /
# setBackgroundColor into the TS entry module.
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
    <title>Status Bar Wiring Demo</title>
  </head>
  <body>
    <main id="app">
      <h1>Status Bar Wiring Demo</h1>
      <p>Install @capacitor/status-bar and wire StatusBar.setStyle / setBackgroundColor here.</p>
    </main>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
EOF

RUN cat >/home/user/myapp/src/main.ts <<'EOF'
// Initial scaffold. The executor must install @capacitor/status-bar v8 and
// add calls to StatusBar.setStyle({ style: Style.Dark }) and
// StatusBar.setBackgroundColor({ color: '#222222' }) here (or in another file
// under src/) so that the resulting bundle still contains those calls.
const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Replace me with a StatusBar wiring integration.";
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

# Pre-existing Capacitor v8 configuration without StatusBar wiring.
RUN cat >/home/user/myapp/capacitor.config.ts <<'EOF'
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.myapp',
  appName: 'Status Bar Wiring Demo',
  webDir: 'dist',
};

export default config;
EOF

# Install all core dependencies up front so the executor only has to add
# @capacitor/status-bar at v8. The initial-state tests check that the plugin
# is absent.
RUN cd /home/user/myapp && npm install --no-audit --no-fund

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 task environment: pre-scaffolded Vite + TypeScript project with Capacitor core/CLI installed; @capacitor/status-bar NOT yet installed."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 (satisfies Capacitor v8 Node 22+ requirement)
#   - pip3 packages for verification: pytest-xprocess, requests
#   - /home/user/myapp: pre-scaffolded Vite + TypeScript + Capacitor v8 project
#       * @capacitor/core and @capacitor/cli installed in node_modules
#       * capacitor.config.ts present (no Status Bar wiring yet)
#       * @capacitor/status-bar NOT installed
#       * src/main.ts scaffold without StatusBar calls
