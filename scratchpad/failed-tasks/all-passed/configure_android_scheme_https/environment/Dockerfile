FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Base toolchain: always-required apt/pip packages, JDK 17 for `cap sync`'s
# Android platform interactions, and Node.js v22 (Capacitor v8 requires Node >= 22).
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep \
        openjdk-17-jdk-headless && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    pip3 install --break-system-packages pytest-json-ctrf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/.harbor

# Scaffold a minimal Vite + Capacitor v8 project at /home/user/myapp.
RUN mkdir -p /home/user/myapp && \
    cat >/home/user/myapp/package.json <<'EOF'
{
  "name": "myapp",
  "private": true,
  "version": "0.0.1",
  "type": "module",
  "scripts": {
    "build": "vite build"
  },
  "devDependencies": {
    "@capacitor/cli": "^8.0.0",
    "tsx": "^4.19.0",
    "typescript": "^5.4.0",
    "vite": "^5.4.0"
  },
  "dependencies": {
    "@capacitor/android": "^8.0.0",
    "@capacitor/core": "^8.0.0"
  }
}
EOF

RUN cat >/home/user/myapp/index.html <<'EOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>My Capacitor App</title>
  </head>
  <body>
    <h1>My Capacitor App</h1>
  </body>
</html>
EOF

RUN cat >/home/user/myapp/tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "esModuleInterop": true,
    "strict": true,
    "skipLibCheck": true,
    "resolveJsonModule": true
  },
  "include": ["capacitor.config.ts"]
}
EOF

# Pre-bootstrap capacitor.config.ts uses the buggy custom Android scheme described
# in the research plan's Friction Point 3. The agent must update server.androidScheme
# to 'https' and add server.hostname = 'myapp.example.com'.
RUN cat >/home/user/myapp/capacitor.config.ts <<'EOF'
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.myapp',
  appName: 'My Capacitor App',
  webDir: 'dist',
  server: {
    androidScheme: 'app'
  }
};

export default config;
EOF

# Install npm dependencies, perform an initial build, then scaffold the Android
# native project so the bootstrap state matches a fully-initialized Capacitor app.
RUN cd /home/user/myapp && \
    npm install --no-audit --no-fund && \
    npm run build && \
    npx --no-install cap add android

# Record the initial appId/appName/webDir for the final-state verifier so it
# can assert these fields are not modified by the agent.
RUN cat >/home/user/.harbor/initial_capacitor_config.json <<'EOF'
{
  "appId": "com.example.myapp",
  "appName": "My Capacitor App",
  "webDir": "dist"
}
EOF

LABEL Author="generate-harbor-tasks"
LABEL Description="Vite + Capacitor v8 project pre-scaffolded at /home/user/myapp with the Android custom-scheme misconfiguration from Friction Point 3."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - openjdk-17-jdk-headless: required by `npx cap sync` for Android platform updates
#   - Node.js v22 (Capacitor v8 requires Node >= 22)
#   - /home/user/myapp: Vite + Capacitor v8 project (package.json, index.html, capacitor.config.ts, tsconfig.json, node_modules, dist, android/)
#   - /home/user/.harbor/initial_capacitor_config.json: snapshot of initial appId/appName/webDir used by the verifier
