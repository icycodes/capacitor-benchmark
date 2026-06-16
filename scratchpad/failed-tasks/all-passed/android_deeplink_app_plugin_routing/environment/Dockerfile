FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV ANDROID_HOME=/opt/android-sdk
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV GRADLE_USER_HOME=/root/.gradle
ENV PATH=/usr/lib/jvm/java-21-openjdk-amd64/bin:/opt/android-sdk/cmdline-tools/latest/bin:/opt/android-sdk/platform-tools:$PATH

# ---------------------------------------------------------------------------
# Base system packages (always-required + this task's runtime extras: unzip,
# JDK 21, fontconfig for Gradle/AGP).
# ---------------------------------------------------------------------------
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep \
        unzip zip xz-utils openjdk-21-jdk-headless fontconfig file && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    pip3 install --break-system-packages pytest-json-ctrf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Node.js v22 (Capacitor v8 requires Node 22+).
# ---------------------------------------------------------------------------
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Android SDK command-line tools + required platform/build-tools for AGP 8.x.
# ---------------------------------------------------------------------------
RUN mkdir -p "${ANDROID_SDK_ROOT}/cmdline-tools" && \
    cd /tmp && \
    curl -fsSL -o cmdline-tools.zip \
        https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip && \
    unzip -q cmdline-tools.zip -d "${ANDROID_SDK_ROOT}/cmdline-tools" && \
    mv "${ANDROID_SDK_ROOT}/cmdline-tools/cmdline-tools" \
       "${ANDROID_SDK_ROOT}/cmdline-tools/latest" && \
    rm -f cmdline-tools.zip && \
    yes | "${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin/sdkmanager" --licenses >/dev/null && \
    "${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin/sdkmanager" \
        "platform-tools" \
        "platforms;android-35" \
        "build-tools;35.0.0" >/dev/null

RUN mkdir -p /home/user && chmod 0755 /home/user

# ---------------------------------------------------------------------------
# Bootstrap the Capacitor v8 project at /home/user/myapp with the Android
# platform already scaffolded and @capacitor/app pre-installed. Capacitor v8
# is pinned to keep the environment reproducible.
# ---------------------------------------------------------------------------
RUN mkdir -p /home/user/myapp /home/user/myapp/dist /home/user/myapp/src && \
    cd /home/user/myapp && \
    cat >package.json <<'JSON'
{
  "name": "myapp",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "build": "echo \"Static dist directory already prepared\""
  }
}
JSON

RUN cat >/home/user/myapp/dist/index.html <<'HTML'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>MyApp</title>
  </head>
  <body>
    <h1>MyApp</h1>
    <p id="route">Loading...</p>
    <script type="module" src="./app.js"></script>
  </body>
</html>
HTML

RUN cat >/home/user/myapp/dist/app.js <<'JS'
console.log("MyApp web shell loaded.");
JS

RUN cat >/home/user/myapp/src/index.ts <<'TS'
// Placeholder web entry. The Capacitor bridge will inject native plugins here.
export {};
TS

# Install Capacitor v8 dependencies (including @capacitor/app), initialize,
# and add the Android platform.
RUN cd /home/user/myapp && \
    npm install --no-audit --no-fund --silent \
        @capacitor/core@^8 @capacitor/android@^8 @capacitor/app@^8 && \
    npm install --no-audit --no-fund --silent -D \
        @capacitor/cli@^8 typescript@^5 && \
    npx --yes cap init "MyApp" "com.example.myapp" --web-dir dist && \
    npx --yes cap add android

# Pre-warm Gradle dependency cache (this also creates the default debug
# keystore at $HOME/.android/debug.keystore, which the verifier uses to
# compute the expected SHA-256 fingerprint for assetlinks.json). After the
# warm-up, drop the build outputs but keep /root/.gradle and the keystore.
RUN cd /home/user/myapp/android && \
    ./gradlew --no-daemon :app:assembleDebug && \
    rm -rf /home/user/myapp/android/app/build \
           /home/user/myapp/android/build \
           /home/user/myapp/android/.gradle && \
    test -f "$HOME/.android/debug.keystore"

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 hybrid app with Android platform scaffolded and @capacitor/app pre-installed under /home/user/myapp, ready for adding Android App Links / deep linking configuration."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - task-specific apt packages: unzip zip xz-utils openjdk-21-jdk-headless fontconfig file
#   - Node.js v22 (Capacitor v8 requirement)
#   - Android command-line tools, platform-tools, platforms;android-35, build-tools;35.0.0
#   - /home/user/myapp: Capacitor v8 project pre-initialized (web-dir=dist)
#   - /home/user/myapp/android: native Android project scaffolded by `npx cap add android`
#   - /home/user/myapp/dist: minimal static web bundle with index.html and app.js
#   - /home/user/myapp/src: TypeScript source directory where the executor adds deeplink.ts
#   - /home/user/myapp/node_modules: @capacitor/core, @capacitor/android, @capacitor/app, @capacitor/cli, typescript
#   - /root/.gradle: pre-warmed Gradle dependency cache (enables --offline builds)
#   - /root/.android/debug.keystore: default Android debug keystore (created by the warm-up build); the verifier reads its SHA-256 fingerprint via keytool
