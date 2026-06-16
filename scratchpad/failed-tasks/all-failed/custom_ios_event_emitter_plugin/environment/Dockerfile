FROM ubuntu:24.04

# --- System & Python dependencies ---
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep \
        unzip xz-utils && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    pip3 install --break-system-packages pytest-json-ctrf && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

# --- Bootstrap a Capacitor v8 project at /home/user/myapp with the iOS platform added ---
# Note: CocoaPods is intentionally NOT installed. Capacitor 8 defaults to Swift Package Manager
# for iOS, and `npx cap sync ios` will skip the pod install step with a warning (still exits 0).
RUN mkdir -p /home/user/myapp/dist && \
    cat >/home/user/myapp/package.json <<'EOF'
{
  "name": "myapp",
  "version": "0.0.1",
  "private": true,
  "scripts": {
    "build": "echo built"
  }
}
EOF

RUN cat >/home/user/myapp/dist/index.html <<'EOF'
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>My App</title>
  </head>
  <body>
    <div id="app"></div>
  </body>
</html>
EOF

RUN cd /home/user/myapp && \
    npm install --no-audit --no-fund --silent \
        @capacitor/core@^8.0.0 \
        @capacitor/cli@^8.0.0 \
        @capacitor/ios@^8.0.0 && \
    npx --no-install cap init "My App" "com.example.myapp" --web-dir dist && \
    npx --no-install cap add ios

# --- Plant a custom MyViewController.swift inside the iOS App group ---
# Mirrors the public Capacitor v8 guide: a CAPBridgeViewController subclass intended
# to host plugin registration via `capacitorDidLoad`. The agent's task is to add the
# capacitorDidLoad override and register the TimerEmitterPlugin instance.
RUN cat >/home/user/myapp/ios/App/App/MyViewController.swift <<'EOF'
import UIKit
import Capacitor

class MyViewController: CAPBridgeViewController {
    // Add Capacitor-specific overrides here, such as capacitorDidLoad() for
    // registering custom local plugins.
}
EOF

# --- Sanity: ensure TimerEmitterPlugin.swift and src/timer-emitter.ts do NOT exist in the initial state ---
RUN test ! -e /home/user/myapp/ios/App/App/TimerEmitterPlugin.swift && \
    test ! -e /home/user/myapp/src/timer-emitter.ts

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 hybrid app pre-scaffolded at /home/user/myapp with the iOS platform added and a custom MyViewController.swift planted (no TimerEmitterPlugin yet)."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 for the Capacitor CLI
#   - /home/user/myapp: Capacitor v8 project with @capacitor/core, @capacitor/cli, @capacitor/ios installed
#       and the iOS platform scaffolded via `npx cap add ios`
#   - /home/user/myapp/ios/App/App/MyViewController.swift: custom CAPBridgeViewController subclass
#       awaiting capacitorDidLoad override + TimerEmitterPlugin registration
#   - CocoaPods is intentionally NOT installed (Capacitor v8 defaults to SPM, and `cap sync ios`
#       skips pod install gracefully without it)
