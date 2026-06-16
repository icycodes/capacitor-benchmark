FROM ubuntu:24.04

# ---------------------------------------------------------------------------
# Base system packages + Node.js 24 (satisfies Capacitor v8's Node 22+ minimum)
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
# Pre-scaffold a minimal Vite + React + TypeScript project at /home/user/myapp.
# The executor must integrate Capacitor v8 on top of this base project.
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
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.3",
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
    <title>React Demo</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOF

RUN cat >/home/user/myapp/src/main.tsx <<'EOF'
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

const rootElement = document.getElementById("root");
if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
}
EOF

RUN cat >/home/user/myapp/src/App.tsx <<'EOF'
import React from "react";

export default function App(): React.ReactElement {
  return (
    <main>
      <h1>React Demo</h1>
      <p>Bootstrapped with Vite + React + TypeScript.</p>
    </main>
  );
}
EOF

RUN cat >/home/user/myapp/vite.config.ts <<'EOF'
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
});
EOF

RUN cat >/home/user/myapp/tsconfig.json <<'EOF'
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
EOF

RUN cat >/home/user/myapp/tsconfig.app.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": false,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "jsx": "react-jsx",
    "strict": true,
    "noEmit": true
  },
  "include": ["src"]
}
EOF

RUN cat >/home/user/myapp/tsconfig.node.json <<'EOF'
{
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "skipLibCheck": true,
    "noEmit": true
  },
  "include": ["vite.config.ts"]
}
EOF

# Install base project dependencies up front so the task environment matches
# the assumptions in test_initial_state.py (node_modules pre-populated).
RUN cd /home/user/myapp && npm install --no-audit --no-fund

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 task environment: pre-scaffolded Vite + React + TypeScript project at /home/user/myapp, ready for the executor to integrate Capacitor v8 non-interactively."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 (satisfies Capacitor v8 Node 22+ requirement)
#   - pip3 packages for verification: pytest-xprocess, requests
#   - /home/user/myapp: pre-scaffolded Vite + React + TypeScript project with node_modules installed
