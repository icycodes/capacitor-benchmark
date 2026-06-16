FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    pip3 install --break-system-packages pytest-json-ctrf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

# Scaffold the hybrid Cordova/Capacitor project at /home/user/myproject.
RUN mkdir -p /home/user/myproject/www/js && \
    cd /home/user/myproject && \
    cat > package.json <<'JSON'
{
  "name": "migration-demo",
  "version": "1.0.0",
  "private": true,
  "description": "Hybrid Cordova/Capacitor demo before migrating off cordova-plugin-device.",
  "scripts": {
    "build": "echo \"build noop (assets are pre-built under www/)\""
  },
  "dependencies": {
    "@capacitor/android": "^8.0.0",
    "@capacitor/core": "^8.0.0",
    "cordova-plugin-device": "^3.0.0"
  },
  "devDependencies": {
    "@capacitor/cli": "^8.0.0"
  }
}
JSON

RUN cd /home/user/myproject && \
    cat > capacitor.config.json <<'JSON'
{
  "appId": "com.example.migrationdemo",
  "appName": "Migration Demo",
  "webDir": "www",
  "cordova": {
    "preferences": {
      "ScrollEnabled": "false"
    }
  }
}
JSON

RUN cd /home/user/myproject && \
    cat > www/index.html <<'HTML'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Migration Demo</title>
  </head>
  <body>
    <h1>Migration Demo</h1>
    <pre id="device-info">Loading device info...</pre>

    <!-- Legacy Cordova bridge: must be removed during the migration -->
    <script src="cordova.js"></script>
    <script src="js/device-info.js"></script>
  </body>
</html>
HTML

RUN cd /home/user/myproject && \
    cat > www/js/device-info.js <<'JS'
// Legacy Cordova device reader. Migrate this to use @capacitor/device.
document.addEventListener('deviceready', function () {
  var d = window.device || {};
  var battery = (window.navigator && window.navigator.battery) || {};

  var payload = {
    uuid: d.uuid,
    model: d.model,
    platform: d.platform,
    version: d.version,
    manufacturer: d.manufacturer,
    isVirtual: d.isVirtual,
    serial: d.serial,
    batteryLevel: battery.level,
    isCharging: battery.charging
  };

  document.getElementById('device-info').textContent = JSON.stringify(payload, null, 2);
}, false);
JS

# Install dependencies (Capacitor core + CLI + android, and the legacy cordova-plugin-device).
RUN cd /home/user/myproject && \
    npm install --no-audit --no-fund --loglevel=error

# Scaffold the Android native project so `npx cap sync` has a platform to sync against.
# `cap add android` only copies template files; it does not require the Android SDK or Java.
RUN cd /home/user/myproject && \
    CI=true npx --no-install cap add android

LABEL Author="generate-harbor-tasks"
LABEL Description="Hybrid Cordova/Capacitor v8 project with cordova-plugin-device pre-installed, ready to be migrated to @capacitor/device."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v22 (via nodesource) for Capacitor v8 tooling
#   - /home/user/myproject: hybrid Cordova/Capacitor demo project
#     - package.json declares @capacitor/core, @capacitor/android, @capacitor/cli, and the legacy cordova-plugin-device
#     - capacitor.config.json with webDir="www"
#     - www/index.html with a <script src="cordova.js"></script> bridge
#     - www/js/device-info.js using the legacy window.device global
#     - node_modules with @capacitor/core, @capacitor/cli, @capacitor/android, cordova-plugin-device installed
#     - android/ native project scaffolded by `npx cap add android`
