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

# Scaffold a Capacitor v8 project with the Android platform added, but WITHOUT
# the @capacitor/push-notifications plugin, FCM Gradle wiring, google-services.json,
# the TypeScript wiring file, or the setup.log.
RUN mkdir -p /home/user/myproject/dist /home/user/myproject/src && \
    cd /home/user/myproject && \
    cat >dist/index.html <<'EOF'
<!doctype html>
<html><head><meta charset="utf-8"><title>Capacitor Push Setup Task</title></head>
<body><h1>Placeholder web assets</h1></body></html>
EOF

RUN cd /home/user/myproject && \
    npm init -y >/dev/null && \
    npm install --no-audit --no-fund \
        @capacitor/core@^8.0.0 \
        @capacitor/android@^8.0.0 && \
    npm install --no-audit --no-fund --save-dev @capacitor/cli@^8.0.0 && \
    npx --yes cap init "My Native App" "com.example.myapp" --web-dir dist && \
    npx --yes cap add android

# Provide a small README-style placeholder in src/ so the directory is present
# but does not yet contain push wiring.
RUN cat >/home/user/myproject/src/index.ts <<'EOF'
// Placeholder entry point. The executor will add src/push.ts to wire up
// @capacitor/push-notifications for Android FCM.
export {};
EOF

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 project scaffolded with Android platform; push-notifications, FCM Gradle wiring, and src/push.ts are NOT yet present."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 (>= v22 required by Capacitor v8) for running the Capacitor CLI
#   - /home/user/myproject: Capacitor v8 project initialised with package id com.example.myapp
#       * dependencies: @capacitor/core ^8, @capacitor/android ^8
#       * devDependencies: @capacitor/cli ^8
#       * dist/index.html: placeholder web assets matching webDir
#       * android/: native Android project scaffolded by `npx cap add android`
#       * src/index.ts: placeholder entry point; src/push.ts must be created by the executor
#   - NOT pre-installed / pre-created (the executor must add these):
#       * @capacitor/push-notifications npm package
#       * google-services Gradle plugin classpath and applied plugin
#       * firebase-messaging implementation dependency
#       * android/app/google-services.json
#       * src/push.ts
#       * /home/user/myproject/setup.log
