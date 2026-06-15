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

# Bootstrap the pre-existing Vite project at /home/user/myproject.
RUN mkdir -p /home/user/myproject/src && \
    cd /home/user/myproject && \
    cat >package.json <<'EOF'
{
  "name": "myproject",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "build": "vite build",
    "dev": "vite"
  },
  "dependencies": {
    "@capacitor/core": "^8.0.0"
  },
  "devDependencies": {
    "@capacitor/cli": "^8.0.0",
    "vite": "^5.4.0"
  }
}
EOF

RUN cd /home/user/myproject && \
    cat >index.html <<'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Harbor Capacitor Test</title>
  </head>
  <body>
    <h1>Harbor Capacitor Test</h1>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
EOF

RUN cd /home/user/myproject && \
    cat >src/main.js <<'EOF'
console.log("Harbor Capacitor Test boot");
EOF

# Install dependencies so @capacitor/core, @capacitor/cli, and vite are available
# in node_modules before the executor begins the task.
RUN cd /home/user/myproject && \
    npm install --no-audit --no-fund --loglevel=error

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 + Vite project pre-installed at /home/user/myproject, not yet initialized with cap init."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v22 (required minimum for Capacitor v8)
#   - /home/user/myproject: pre-existing Vite project
#     - package.json declaring vite, @capacitor/core@^8, @capacitor/cli@^8
#     - index.html: Vite entry document
#     - src/main.js: trivial Vite source file
#     - node_modules/: populated via `npm install` so @capacitor/cli (cap),
#       @capacitor/core, and vite are usable immediately
#   - Capacitor is intentionally NOT initialized: no capacitor.config.* file exists yet
