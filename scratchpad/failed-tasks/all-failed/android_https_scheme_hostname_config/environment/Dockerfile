FROM ubuntu:24.04

# --- System packages, Python, and Node.js 22 (Capacitor v8 requires Node 22+) ---
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep \
        xz-utils gnupg && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends nodejs && \
    pip3 install --break-system-packages pytest-json-ctrf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

# --- Bootstrap a Capacitor v8 project at /home/user/myapp ---
# Layout produced here:
#   /home/user/myapp/package.json     - declares @capacitor/{core,cli,android} v8 deps
#   /home/user/myapp/capacitor.config.ts
#       - exports appId/appName/webDir but NO `server` block yet
#   /home/user/myapp/dist/index.html  - pre-built web assets for `cap sync`
#   /home/user/myapp/android/         - native Android project (via `npx cap add android`)
#   /home/user/myapp/node_modules/    - populated by `npm install`
RUN mkdir -p /home/user/myapp/dist && \
    cd /home/user/myapp && \
    cat >package.json <<'EOF'
{
  "name": "myapp",
  "version": "1.0.0",
  "private": true,
  "description": "Pre-bootstrapped Capacitor v8 project for the android_https_scheme_hostname_config task.",
  "scripts": {
    "build": "echo \"web assets already built into dist/\""
  },
  "dependencies": {
    "@capacitor/android": "^8.0.0",
    "@capacitor/core": "^8.0.0"
  },
  "devDependencies": {
    "@capacitor/cli": "^8.0.0"
  }
}
EOF

RUN cd /home/user/myapp && \
    cat >capacitor.config.ts <<'EOF'
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.myapp',
  appName: 'My Native App',
  webDir: 'dist',
};

export default config;
EOF

RUN cd /home/user/myapp/dist && \
    cat >index.html <<'EOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>My Native App</title>
  </head>
  <body>
    <h1>Hello from Capacitor</h1>
  </body>
</html>
EOF

# Install Capacitor dependencies and add the Android platform.
RUN cd /home/user/myapp && \
    npm install --no-audit --no-fund --loglevel=error && \
    npx --no-install cap add android

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 sandbox project at /home/user/myapp pre-bootstrapped with the Android platform added but no custom server.androidScheme/hostname or network security config."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v22 (Capacitor v8 requirement) installed from NodeSource
#   - /home/user/myapp: Capacitor v8 project root
#       * package.json declaring @capacitor/{core,cli,android} ^8
#       * capacitor.config.ts with appId/appName/webDir but no `server` block (executor must add it)
#       * dist/index.html prebuilt web assets
#       * android/ native project (added via `npx cap add android`)
#       * node_modules/ populated by `npm install`
