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
# Pre-warm the npm and Gradle caches by running the same bootstrap flow that
# the task expects, then deleting the resulting project directory. This keeps
# the starting environment empty (so test_initial_state.py passes), while
# letting the executor install/build/sync quickly inside the container.
# ---------------------------------------------------------------------------
RUN mkdir -p /tmp/prewarm && \
    cd /tmp/prewarm && \
    npm create vite@latest myapp -- --template react-ts && \
    cd myapp && \
    npm install --no-audit --no-fund --silent && \
    npm install --no-audit --no-fund --silent \
        @capacitor/core@^8 @capacitor/android@^8 && \
    npm install --no-audit --no-fund --silent -D @capacitor/cli@^8 && \
    npx --yes cap init "My App" "com.example.myapp" --web-dir dist && \
    npx --yes cap add android && \
    cd android && \
    ./gradlew --no-daemon help >/dev/null && \
    cd / && \
    rm -rf /tmp/prewarm

# ---------------------------------------------------------------------------
# Create the empty workspace directory where the executor will scaffold the
# Capacitor v8 + Vite project from scratch.
# ---------------------------------------------------------------------------
RUN mkdir -p /home/user/workspace && chmod 0755 /home/user/workspace

LABEL Author="generate-harbor-tasks"
LABEL Description="Empty /home/user/workspace ready for the executor to bootstrap a Vite + React + TypeScript Capacitor v8 Android project from scratch. Node 22, JDK 21, Android SDK 35, and pre-warmed npm/Gradle caches are provisioned."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - task-specific apt packages: unzip zip xz-utils openjdk-21-jdk-headless fontconfig file
#   - Node.js v22 (Capacitor v8 requirement)
#   - Android command-line tools, platform-tools, platforms;android-35, build-tools;35.0.0
#   - pre-warmed npm cache (/root/.npm) and Gradle cache (/root/.gradle) so
#     scaffolding + cap add android run quickly inside the container
#   - /home/user/workspace: empty directory where the executor scaffolds /home/user/workspace/myapp
