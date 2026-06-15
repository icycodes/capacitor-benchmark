FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    pip3 install --break-system-packages pytest-json-ctrf requests && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

# ----- Bootstrap a Capacitor v8 project skeleton at /home/user/myproject -----
RUN mkdir -p /home/user/myproject /home/user/myproject/dist /home/user/myproject/scripts && \
    cd /home/user/myproject && \
    cat >package.json <<'EOF'
{
  "name": "myproject",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "build": "echo \"static assets already in ./dist\"",
    "http-cli": "tsx scripts/http-cli.ts"
  },
  "dependencies": {
    "@capacitor/core": "^8.0.0"
  },
  "devDependencies": {
    "@capacitor/cli": "^8.0.0",
    "tsx": "^4.19.2",
    "typescript": "^5.4.5"
  }
}
EOF

RUN cd /home/user/myproject && \
    cat >tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "types": ["node"]
  },
  "include": ["scripts/**/*.ts", "capacitor.config.ts"]
}
EOF

RUN cd /home/user/myproject && \
    cat >dist/index.html <<'EOF'
<!doctype html>
<html><head><meta charset="utf-8"><title>My Native App</title></head>
<body><h1>Capacitor placeholder</h1></body></html>
EOF

# Install dependencies (network) so the initial state mirrors a `npm install`-ed project.
RUN cd /home/user/myproject && npm install --no-audit --no-fund

# Initialize Capacitor non-interactively (creates capacitor.config.ts with no plugins section).
RUN cd /home/user/myproject && \
    npx --yes cap init "My Native App" "com.example.myapp" --web-dir dist

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 project skeleton (Node 22) for the CapacitorHttp CORS-bypass task."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf, requests (for verification)
#   - Node.js v22 (Capacitor v8 minimum) installed via NodeSource
#   - /home/user/myproject: Capacitor v8 project skeleton
#       * package.json with @capacitor/core, @capacitor/cli, tsx, typescript
#       * node_modules installed via `npm install`
#       * capacitor.config.ts generated via `npx cap init` (CapacitorHttp NOT yet enabled)
#       * dist/index.html placeholder web asset
#       * scripts/ directory (empty — agent must create scripts/http-cli.ts)
