FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    pip3 install --break-system-packages pytest-json-ctrf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

# ----------------------------------------------------------------------------
# Bootstrap a Capacitor v8 project at /home/user/myproject with all
# dependencies already installed.  The CapacitorHttp plugin is NOT yet
# enabled and the helper module is NOT yet present — the task executor is
# expected to add both.
# ----------------------------------------------------------------------------
RUN mkdir -p /home/user/myproject/src /home/user/myproject/dist && \
    cd /home/user/myproject && \
    cat >dist/index.html <<'EOF'
<!doctype html>
<html><head><meta charset="utf-8"><title>Placeholder</title></head>
<body><p>placeholder web bundle</p></body></html>
EOF

RUN cd /home/user/myproject && \
    cat >package.json <<'EOF'
{
  "name": "myproject",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "build": "tsc --noEmit -p tsconfig.json"
  }
}
EOF

RUN cd /home/user/myproject && \
    cat >tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "rootDir": "src",
    "outDir": "build",
    "types": []
  },
  "include": ["src/**/*.ts", "capacitor.config.ts"]
}
EOF

RUN cd /home/user/myproject && \
    npm install --silent --no-audit --no-fund \
        @capacitor/core@^8.0.0 \
        @capacitor/preferences@^8.0.0 && \
    npm install --silent --no-audit --no-fund --save-dev \
        @capacitor/cli@^8.0.0 \
        typescript@^5.4.0 && \
    npx --no-install cap init "My Native App" "com.example.myapp" --web-dir dist

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 project pre-bootstrapped at /home/user/myproject with @capacitor/core, @capacitor/cli, @capacitor/preferences, and TypeScript; CapacitorHttp plugin not yet enabled."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 (for Capacitor v8, which requires Node >= 22)
#   - /home/user/myproject: Capacitor v8 project root
#     - package.json (with "build" script -> tsc --noEmit -p tsconfig.json)
#     - tsconfig.json (strict, NodeNext modules)
#     - capacitor.config.ts (appId com.example.myapp, appName "My Native App", webDir dist; NO CapacitorHttp plugin yet)
#     - src/ (empty; executor adds src/api/httpClient.ts)
#     - dist/ with placeholder index.html
#     - node_modules with @capacitor/core, @capacitor/preferences, @capacitor/cli, typescript
