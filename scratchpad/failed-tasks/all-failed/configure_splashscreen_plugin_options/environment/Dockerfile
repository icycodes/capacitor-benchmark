FROM ubuntu:24.04

# ---------------------------------------------------------------------------
# Base system packages + Node.js 24 (satisfies Capacitor v8's Node 22+ minimum).
# No browser verification is required for this task: the final-state check
# evaluates the Capacitor config via `npx tsx` and inspects the build output.
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
# Pre-scaffold a Vite + TypeScript + Capacitor v8 project at /home/user/myapp.
# The agent must install @capacitor/splash-screen@^8, populate the
# plugins.SplashScreen options, and call SplashScreen.hide() from src/.
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
    <title>SplashScreen Demo</title>
  </head>
  <body>
    <main id="app">
      <h1>SplashScreen Demo</h1>
      <p>Install @capacitor/splash-screen and hide the splash here.</p>
    </main>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
EOF

RUN cat >/home/user/myapp/src/main.ts <<'EOF'
// Initial scaffold. The executor must install @capacitor/splash-screen@^8,
// configure plugins.SplashScreen in capacitor.config.ts, and call
// SplashScreen.hide() from a TS module after the DOM is ready.
const app = document.getElementById("app");
if (app) {
  const note = document.createElement("p");
  note.textContent = "Replace me with a SplashScreen.hide() call.";
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

# Pre-existing Capacitor v8 configuration WITHOUT the SplashScreen plugin block.
RUN cat >/home/user/myapp/capacitor.config.ts <<'EOF'
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.myapp',
  appName: 'SplashScreen Demo',
  webDir: 'dist',
};

export default config;
EOF

# Install dependencies up front so the initial state matches the expectations
# encoded in test_initial_state.py (node_modules present, @capacitor/core +
# @capacitor/cli on disk, @capacitor/splash-screen NOT installed).
RUN cd /home/user/myapp && npm install --no-audit --no-fund

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 task environment: pre-scaffolded Vite + TypeScript project with Capacitor installed; @capacitor/splash-screen is intentionally absent so the agent must install and configure it."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 (satisfies Capacitor v8 Node 22+ requirement)
#   - /home/user/myapp: pre-scaffolded Vite + TypeScript + Capacitor v8 project
#       * @capacitor/core and @capacitor/cli installed in node_modules
#       * capacitor.config.ts present WITHOUT a plugins.SplashScreen block
#       * src/main.ts present WITHOUT any @capacitor/splash-screen import
#       * @capacitor/splash-screen intentionally NOT installed
