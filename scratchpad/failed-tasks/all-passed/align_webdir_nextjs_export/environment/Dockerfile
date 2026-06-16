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

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

RUN mkdir -p /home/user && chmod 0755 /home/user

# Scaffold a deterministic Next.js 14 + TypeScript project at /home/user/myapp.
# Capacitor v8 (core, CLI, and the Android platform) is pre-installed but
# misconfigured: capacitor.config.ts already declares webDir: "out", while
# next.config.js does NOT enable static export, so `next build` only produces
# the `.next/` directory. As a result, `npm run build && npx cap sync` fails
# until the agent enables `output: 'export'` in next.config.js.
RUN mkdir -p /home/user/myapp/src/app && \
    cd /home/user/myapp && \
    cat >package.json <<'EOF'
{
  "name": "myapp",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.2.15",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "@capacitor/core": "^8.0.0",
    "@capacitor/android": "^8.0.0"
  },
  "devDependencies": {
    "@capacitor/cli": "^8.0.0",
    "@types/node": "20.12.12",
    "@types/react": "18.3.3",
    "@types/react-dom": "18.3.0",
    "typescript": "5.4.5"
  }
}
EOF

RUN cd /home/user/myapp && \
    cat >next.config.js <<'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

module.exports = nextConfig;
EOF

RUN cd /home/user/myapp && \
    cat >tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2017",
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
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
EOF

RUN cd /home/user/myapp && \
    cat >next-env.d.ts <<'EOF'
/// <reference types="next" />
/// <reference types="next/image-types/global" />
EOF

RUN cd /home/user/myapp && \
    cat >src/app/layout.tsx <<'EOF'
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MyApp",
  description: "Capacitor + Next.js benchmark fixture",
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
EOF

RUN cd /home/user/myapp && \
    cat >src/app/page.tsx <<'EOF'
export default function Page() {
  return (
    <main>
      <h1>Hello from Capacitor benchmark</h1>
    </main>
  );
}
EOF

RUN cd /home/user/myapp && \
    cat >capacitor.config.ts <<'EOF'
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.myapp',
  appName: 'MyApp',
  webDir: 'out',
};

export default config;
EOF

# Install JS dependencies and add the Android native project so `npx cap sync`
# actually exercises the webDir copy step during verification.
RUN cd /home/user/myapp && \
    npm install --no-audit --no-fund --loglevel=error && \
    mkdir -p out && \
    echo '<!doctype html><html><body>placeholder</body></html>' > out/index.html && \
    npx --no-install cap add android && \
    rm -rf out

LABEL Author="generate-harbor-tasks"
LABEL Description="Next.js 14 + Capacitor v8 fixture with mismatched static-export configuration for the align_webdir_nextjs_export task."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - OpenJDK 21 (for Capacitor Android sync compatibility)
#   - Node.js v22 (Capacitor v8 minimum)
#   - /home/user/myapp: Next.js 14 + TypeScript project pre-installed with
#       @capacitor/core@^8, @capacitor/cli@^8, and @capacitor/android@^8.
#       capacitor.config.ts declares webDir: "out", while next.config.js is
#       MISSING `output: 'export'`, so `npm run build && npx cap sync` fails
#       until the agent fixes the Next.js configuration.
#   - /home/user/myapp/android: pre-scaffolded native Android project so
#       `npx cap sync` triggers the webDir copy step during verification.
