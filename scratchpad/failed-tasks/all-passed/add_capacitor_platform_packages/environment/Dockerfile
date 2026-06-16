FROM ubuntu:24.04

# ---------------------------------------------------------------------------
# Base system packages + Node.js 24 (satisfies Capacitor v8's Node 22+ minimum).
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
# Pre-scaffold a minimal Vite + TypeScript project at /home/user/myapp that
# already has Capacitor v8 core + CLI installed and a capacitor.config.ts
# pointing at Vite's `dist` build output. The native platform packages
# (@capacitor/android and @capacitor/ios) are intentionally NOT installed —
# the executor must add them.
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
    <title>Capacitor Platforms Demo</title>
  </head>
  <body>
    <main id="app">
      <h1>Capacitor Platforms Demo</h1>
    </main>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
EOF

RUN cat >/home/user/myapp/src/main.ts <<'EOF'
// Minimal entrypoint. No runtime Capacitor APIs are required for this task —
// the task only verifies the presence and version of installed platform packages.
const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Capacitor platform packages demo.";
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

# Pre-create the Capacitor configuration so the executor only needs to add the
# native platform packages. webDir is aligned with Vite's default `dist` output.
RUN cat >/home/user/myapp/capacitor.config.ts <<'EOF'
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.platformsdemo',
  appName: 'Platforms Demo',
  webDir: 'dist'
};

export default config;
EOF

# Install dependencies (only @capacitor/core, @capacitor/cli, Vite, TypeScript)
# so the initial state matches the assumptions in test_initial_state.py.
RUN cd /home/user/myapp && npm install --no-audit --no-fund

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 task environment: Vite + TS project at /home/user/myapp with @capacitor/core and @capacitor/cli (v8) pre-installed and capacitor.config.ts in place; @capacitor/android and @capacitor/ios are intentionally NOT installed."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 (satisfies Capacitor v8 Node 22+ requirement)
#   - /home/user/myapp: pre-scaffolded Vite + TypeScript project with @capacitor/core and @capacitor/cli v8 installed; capacitor.config.ts present
#   - @capacitor/android and @capacitor/ios are NOT pre-installed (the executor must add them)
