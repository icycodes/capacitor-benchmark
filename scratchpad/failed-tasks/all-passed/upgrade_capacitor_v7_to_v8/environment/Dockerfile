FROM ubuntu:24.04

# ---------------------------------------------------------------------------
# Base system packages + Node.js 24 (satisfies Capacitor v8's Node 22+ minimum
# as well as Capacitor v7's older floor).
# ---------------------------------------------------------------------------
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    pip3 install --break-system-packages \
        pytest-json-ctrf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

# ---------------------------------------------------------------------------
# Pre-scaffold a Vite + TypeScript project at /home/user/myapp that is fully
# wired up against Capacitor v7. The executor must perform the v7 -> v8
# upgrade.
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
  "dependencies": {
    "@capacitor/core": "^7.0.0",
    "@capacitor/preferences": "^7.0.0"
  },
  "devDependencies": {
    "@capacitor/cli": "^7.0.0",
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
    <title>Capacitor v7 -> v8 Upgrade Demo</title>
  </head>
  <body>
    <main id="app">
      <h1>Capacitor v7 -> v8 Upgrade Demo</h1>
    </main>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
EOF

# Source code that imports @capacitor/preferences so that the upgrade must
# preserve compile-time compatibility (the v8 plugin keeps the same JS API
# shape, so this should keep building).
RUN cat >/home/user/myapp/src/main.ts <<'EOF'
import { Preferences } from "@capacitor/preferences";

async function saveTheme(theme: "dark" | "light"): Promise<void> {
  await Preferences.set({ key: "user_theme", value: theme });
}

async function loadTheme(): Promise<string | null> {
  const { value } = await Preferences.get({ key: "user_theme" });
  return value;
}

const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Capacitor v7 -> v8 upgrade demo.";
  app.appendChild(note);
}

// Expose helpers on window for ad-hoc inspection.
(window as unknown as Record<string, unknown>).saveTheme = saveTheme;
(window as unknown as Record<string, unknown>).loadTheme = loadTheme;
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

# Pre-create the Capacitor configuration. The executor MUST keep these
# values (appId / appName / webDir) unchanged. The snapshot file written
# below is what the verifier compares against.
RUN cat >/home/user/myapp/capacitor.config.ts <<'EOF'
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.upgradedemo',
  appName: 'Upgrade Demo',
  webDir: 'dist'
};

export default config;
EOF

# Install dependencies so the project boots in a v7 state matching what the
# initial-state test verifies. The executor must upgrade everything to v8.
RUN cd /home/user/myapp && npm install --no-audit --no-fund

# Persist a JSON snapshot of the initial appId / appName / webDir so the
# final-state verifier can confirm the executor did not modify them. The
# Dockerfile is the canonical source of truth for these values.
RUN mkdir -p /home/user/.harbor && \
    cat >/home/user/.harbor/initial_capacitor_config.json <<'EOF'
{
  "appId": "com.example.upgradedemo",
  "appName": "Upgrade Demo",
  "webDir": "dist"
}
EOF

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v7 task environment: Vite + TS project at /home/user/myapp with @capacitor/core, @capacitor/cli, and @capacitor/preferences pinned to ^7.0.0 (installed). Executor must upgrade everything to Capacitor v8."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 (satisfies Capacitor v7 AND v8 Node.js minimums)
#   - /home/user/myapp: Vite + TypeScript project with @capacitor/core@^7, @capacitor/cli@^7, @capacitor/preferences@^7 installed; capacitor.config.ts present
#   - /home/user/.harbor/initial_capacitor_config.json: JSON snapshot of the initial appId/appName/webDir values (used by the verifier)
