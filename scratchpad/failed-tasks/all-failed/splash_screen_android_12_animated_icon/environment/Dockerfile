FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep \
        openjdk-21-jdk-headless && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    pip3 install --break-system-packages pytest-json-ctrf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

# ----- Scaffold a Capacitor v8 project at /home/user/myproject -----
RUN mkdir -p /home/user/myproject/src /home/user/myproject/dist && \
    mkdir -p /home/user/myproject/android/app/src/main/res/values \
             /home/user/myproject/android/app/src/main/res/drawable \
             /home/user/myproject/android/app/src/main/res/layout

WORKDIR /home/user/myproject

# package.json -- pinned to Capacitor v8 line
RUN cat >/home/user/myproject/package.json <<'EOF'
{
  "name": "my-native-app",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "build": "echo \"web assets already built\""
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

# Capacitor config (no SplashScreen entry yet)
RUN cat >/home/user/myproject/capacitor.config.json <<'EOF'
{
  "appId": "com.example.mynativeapp",
  "appName": "My Native App",
  "webDir": "dist"
}
EOF

# Built web asset (so `cap sync` has something to copy if the executor runs it)
RUN cat >/home/user/myproject/dist/index.html <<'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>My Native App</title>
  </head>
  <body>
    <div id="root">Loading...</div>
    <script type="module" src="./main.js"></script>
  </body>
</html>
EOF

# Minimal "built" JS placeholder
RUN cat >/home/user/myproject/dist/main.js <<'EOF'
console.log('hello from capacitor');
EOF

# Web entry point that the executor must edit
RUN cat >/home/user/myproject/src/main.ts <<'EOF'
// Entry point for the web app. The Android 12+ splash screen behavior is
// controlled here: the executor must import @capacitor/splash-screen and
// call SplashScreen.hide() only after the browser has painted the first frame.
//
// Hint: nest two requestAnimationFrame() calls so the hide() happens AFTER the
// first paint, not before it.

function bootstrap(): void {
  const root = document.getElementById('root');
  if (root) {
    root.textContent = 'Welcome to My Native App';
  }
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
}
EOF

# Android styles.xml -- launch theme already uses Theme.SplashScreen but has no
# Android 12+ attributes yet.
RUN cat >/home/user/myproject/android/app/src/main/res/values/styles.xml <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>

    <style name="AppTheme" parent="Theme.AppCompat.DayNight.NoActionBar">
        <item name="colorPrimary">@color/colorPrimary</item>
        <item name="colorPrimaryDark">@color/colorPrimaryDark</item>
        <item name="colorAccent">@color/colorAccent</item>
    </style>

    <style name="AppTheme.NoActionBar" parent="Theme.AppCompat.DayNight.NoActionBar">
        <item name="windowActionBar">false</item>
        <item name="windowNoTitle">true</item>
        <item name="android:background">@null</item>
    </style>

    <style name="AppTheme.NoActionBarLaunch" parent="Theme.SplashScreen">
        <item name="android:background">@drawable/splash</item>
    </style>

</resources>
EOF

# Default `splash` drawable that ships with Capacitor (a simple vector reference)
RUN cat >/home/user/myproject/android/app/src/main/res/drawable/splash.xml <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@android:color/white"/>
</layer-list>
EOF

# colors.xml so styles.xml references resolve when read by tooling.
RUN cat >/home/user/myproject/android/app/src/main/res/values/colors.xml <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="colorPrimary">#3880FF</color>
    <color name="colorPrimaryDark">#3171E0</color>
    <color name="colorAccent">#7044FF</color>
</resources>
EOF

# Install dependencies (Capacitor v8). Use --ignore-scripts to avoid optional
# post-install hooks that may require the Android SDK.
RUN cd /home/user/myproject && \
    npm install --no-audit --no-fund --ignore-scripts

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 project pre-scaffolded for an Android 12+ animated splash screen configuration task."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - openjdk-21-jdk-headless (Capacitor v8 requires JDK 21)
#   - Node.js v22 (Capacitor v8 minimum) installed via NodeSource
#   - /home/user/myproject: scaffolded Capacitor v8 project with Android platform
#       - package.json declares @capacitor/{core,cli,android} ^8.0.0 (no @capacitor/splash-screen)
#       - capacitor.config.json without a plugins.SplashScreen entry
#       - src/main.ts web entry point that the executor must extend
#       - dist/ contains pre-built web assets
#       - android/app/src/main/res/values/styles.xml has AppTheme.NoActionBarLaunch using parent Theme.SplashScreen
#       - android/app/src/main/res/drawable/ exists (only the default splash.xml present)
#       - node_modules installed with --ignore-scripts so Capacitor v8 packages are available offline
