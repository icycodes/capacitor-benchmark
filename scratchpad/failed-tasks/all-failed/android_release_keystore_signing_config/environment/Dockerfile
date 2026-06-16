FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV ANDROID_HOME=/opt/android-sdk
ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV PATH=/opt/android-sdk/cmdline-tools/latest/bin:/opt/android-sdk/platform-tools:/usr/lib/jvm/java-21-openjdk-amd64/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV GRADLE_USER_HOME=/root/.gradle

# Base OS packages + Java 21 + Node.js v24 + Python deps
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep \
        openjdk-21-jdk-headless unzip xz-utils && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    pip3 install --break-system-packages pytest-json-ctrf && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Android SDK: cmdline-tools + platform-tools + build-tools 35.0.0 + android-35 platform
RUN mkdir -p /opt/android-sdk/cmdline-tools && \
    cd /tmp && \
    curl -fsSL -o cmdline-tools.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip && \
    unzip -q cmdline-tools.zip -d /opt/android-sdk/cmdline-tools && \
    mv /opt/android-sdk/cmdline-tools/cmdline-tools /opt/android-sdk/cmdline-tools/latest && \
    rm cmdline-tools.zip && \
    yes | /opt/android-sdk/cmdline-tools/latest/bin/sdkmanager --licenses > /dev/null && \
    /opt/android-sdk/cmdline-tools/latest/bin/sdkmanager \
        "platform-tools" \
        "platforms;android-35" \
        "build-tools;35.0.0" > /dev/null

# User home
RUN mkdir -p /home/user && chmod 0755 /home/user

# Bootstrap a Capacitor v8 web app and add the Android platform.
# Use a minimal dist/ directory so `npx cap add android` and `npx cap sync` succeed.
RUN mkdir -p /home/user/myproject && \
    cd /home/user/myproject && \
    npm init -y && \
    npm install --no-audit --no-fund @capacitor/core@^8 && \
    npm install --no-audit --no-fund -D @capacitor/cli@^8 && \
    npm install --no-audit --no-fund @capacitor/android@^8 && \
    mkdir -p dist && \
    printf '<!doctype html><html><head><meta charset="utf-8"><title>Capacitor Benchmark</title></head><body><h1>Hello</h1></body></html>\n' > dist/index.html && \
    npx --no-install cap init "Capacitor Benchmark" "com.example.benchmark" --web-dir dist && \
    npx --no-install cap add android

# Pre-warm Gradle so `./gradlew help --offline` works without network access.
# We tolerate transient failures here; the final-state test re-runs gradle.
RUN cd /home/user/myproject/android && \
    chmod +x gradlew && \
    ./gradlew help -q --no-daemon || true && \
    ./gradlew help -q --no-daemon

# Initialize a git repo so `git check-ignore` works against the project's
# .gitignore rules. Make an initial commit of the bootstrapped tree.
RUN cd /home/user/myproject && \
    git init -q -b main && \
    git config user.email "bench@example.com" && \
    git config user.name "bench" && \
    printf 'node_modules/\n' > .gitignore && \
    git add -A && \
    git -c commit.gpgsign=false commit -q -m "bootstrap capacitor v8 android project"

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 Android project bootstrapped at /home/user/myproject with Java 21, Android SDK 35, Node.js v24, and a pre-warmed Gradle cache for offline build script evaluation."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep openjdk-21-jdk-headless unzip xz-utils nodejs
#   - pip3 packages: pytest-json-ctrf
#   - Android SDK at /opt/android-sdk (cmdline-tools, platform-tools, build-tools;35.0.0, platforms;android-35)
#   - Java 21 OpenJDK (headless) for keytool and Gradle
#   - Node.js v24 and Capacitor v8 CLI/core/android plugins
#   - /home/user/myproject: bootstrapped Capacitor v8 project with /android scaffold and a pre-warmed Gradle cache
#   - Git repository initialized at /home/user/myproject for .gitignore verification
