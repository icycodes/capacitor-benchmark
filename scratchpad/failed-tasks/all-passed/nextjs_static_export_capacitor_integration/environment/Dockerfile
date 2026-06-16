FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV ANDROID_HOME=/opt/android-sdk
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH=/usr/lib/jvm/java-21-openjdk-amd64/bin:/opt/android-sdk/cmdline-tools/latest/bin:/opt/android-sdk/platform-tools:$PATH
ENV NEXT_TELEMETRY_DISABLED=1

# ---------------------------------------------------------------------------
# Base system packages plus the JDK + tools required by Capacitor's Android
# scaffolder (`npx cap add android`) and `npx cap sync android`.
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
# Android SDK command-line tools + minimum platform/build-tools needed by
# the Capacitor Android template that `cap add android` scaffolds.
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
# Bootstrap a minimal Next.js 14 (App Router, TypeScript) project at
# /home/user/myapp. Capacitor is intentionally NOT installed — the executor
# is responsible for installing it and wiring the static export + Android
# native platform.
# ---------------------------------------------------------------------------
RUN mkdir -p /home/user/myapp/app /home/user/myapp/public && \
    cd /home/user/myapp && \
    cat >package.json <<'JSON'
{
  "name": "myapp",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.2.15",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "typescript": "^5.4.5",
    "@types/node": "^20.12.7",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0"
  }
}
JSON

RUN cat >/home/user/myapp/tsconfig.json <<'JSON'
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
JSON

RUN cat >/home/user/myapp/next.config.js <<'JS'
/** @type {import('next').NextConfig} */
const nextConfig = {};

module.exports = nextConfig;
JS

RUN cat >/home/user/myapp/next-env.d.ts <<'TS'
/// <reference types="next" />
/// <reference types="next/image-types/global" />
TS

RUN cat >/home/user/myapp/app/layout.tsx <<'TSX'
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MyApp",
  description: "Next.js + Capacitor demo",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
TSX

RUN cat >/home/user/myapp/app/page.tsx <<'TSX'
export default function HomePage() {
  return (
    <main>
      <h1>Hello from MyApp</h1>
      <p>This page will be statically exported for Capacitor.</p>
    </main>
  );
}
TSX

# Install the existing web dependencies (Next.js + React) but NOT Capacitor.
RUN cd /home/user/myapp && \
    npm install --no-audit --no-fund --silent

LABEL Author="generate-harbor-tasks"
LABEL Description="Next.js 14 (App Router, TS) skeleton at /home/user/myapp without Capacitor; Node 22, JDK 21, and Android SDK are pre-installed so the executor can integrate Capacitor v8 and scaffold the Android platform."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - task-specific apt packages: unzip zip xz-utils openjdk-21-jdk-headless fontconfig file
#   - Node.js v22 (Capacitor v8 requirement)
#   - Android command-line tools, platform-tools, platforms;android-35, build-tools;35.0.0
#   - /home/user/myapp: Next.js 14 App Router + TypeScript skeleton, no Capacitor installed yet
#   - /home/user/myapp/node_modules: pre-installed next 14, react, react-dom
