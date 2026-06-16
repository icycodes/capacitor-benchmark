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

# Install a Linux-compatible `plutil` wrapper backed by Python's plistlib.
# Supports the `-lint` sub-command used by Apple's macOS tool, exiting 0 on
# success and printing a `<file>: OK` line that matches the macOS format.
RUN cat >/usr/local/bin/plutil <<'PLUTIL_EOF' && chmod +x /usr/local/bin/plutil
#!/usr/bin/env python3
"""Minimal `plutil` replacement for Linux task environments.

Supports:
    plutil -lint <file>...
"""
import plistlib
import sys


def main(argv):
    if len(argv) < 2:
        print("plutil: missing arguments", file=sys.stderr)
        return 64
    sub = argv[1]
    if sub != "-lint":
        print(f"plutil: subcommand not supported in this environment: {sub}", file=sys.stderr)
        return 64
    files = argv[2:]
    if not files:
        print("plutil: no input file specified", file=sys.stderr)
        return 64
    exit_code = 0
    for path in files:
        try:
            with open(path, "rb") as fp:
                plistlib.load(fp)
            print(f"{path}: OK")
        except FileNotFoundError:
            print(f"{path}: file does not exist", file=sys.stderr)
            exit_code = 1
        except Exception as exc:  # noqa: BLE001
            print(f"{path}: {exc}", file=sys.stderr)
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
PLUTIL_EOF

RUN mkdir -p /home/user && chmod 0755 /home/user

# Scaffold the Capacitor v8 project at /home/user/myapp with:
#   * capacitor.config.ts already containing appId/appName/webDir (no ios block).
#   * ios/App/App/Info.plist matching the default `npx cap add ios` output, but
#     intentionally MISSING the four NS*UsageDescription keys the executor
#     must add.
RUN mkdir -p /home/user/myapp/ios/App/App && \
    mkdir -p /home/user/myapp/dist

RUN cat >/home/user/myapp/capacitor.config.ts <<'CAPCFG_EOF'
import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.myapp',
  appName: 'My Native App',
  webDir: 'dist',
};

export default config;
CAPCFG_EOF

RUN cat >/home/user/myapp/ios/App/App/Info.plist <<'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDevelopmentRegion</key>
	<string>en</string>
	<key>CFBundleDisplayName</key>
	<string>MyApp</string>
	<key>CFBundleExecutable</key>
	<string>$(EXECUTABLE_NAME)</string>
	<key>CFBundleIdentifier</key>
	<string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
	<key>CFBundleInfoDictionaryVersion</key>
	<string>6.0</string>
	<key>CFBundleName</key>
	<string>$(PRODUCT_NAME)</string>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleShortVersionString</key>
	<string>1.0</string>
	<key>CFBundleVersion</key>
	<string>1</string>
	<key>LSRequiresIPhoneOS</key>
	<true/>
	<key>UILaunchStoryboardName</key>
	<string>LaunchScreen</string>
	<key>UIMainStoryboardFile</key>
	<string>Main</string>
	<key>UIRequiredDeviceCapabilities</key>
	<array>
		<string>armv7</string>
	</array>
	<key>UISupportedInterfaceOrientations</key>
	<array>
		<string>UIInterfaceOrientationPortrait</string>
		<string>UIInterfaceOrientationLandscapeLeft</string>
		<string>UIInterfaceOrientationLandscapeRight</string>
	</array>
	<key>UISupportedInterfaceOrientations~ipad</key>
	<array>
		<string>UIInterfaceOrientationPortrait</string>
		<string>UIInterfaceOrientationPortraitUpsideDown</string>
		<string>UIInterfaceOrientationLandscapeLeft</string>
		<string>UIInterfaceOrientationLandscapeRight</string>
	</array>
	<key>UIViewControllerBasedStatusBarAppearance</key>
	<true/>
</dict>
</plist>
PLIST_EOF

LABEL Author="generate-harbor-tasks"
LABEL Description="Capacitor v8 iOS project preconfigured at /home/user/myapp with a default Info.plist (missing NS*UsageDescription keys) and capacitor.config.ts without an ios block. Includes a Linux plutil wrapper for plist validation."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js 22 (for evaluating capacitor.config.ts during verification)
#   - /usr/local/bin/plutil: Linux wrapper backed by Python plistlib (supports `-lint`)
#   - /home/user/myapp: pre-scaffolded Capacitor v8 project
#   - /home/user/myapp/capacitor.config.ts: TS config with appId/appName/webDir, no `ios` block yet
#   - /home/user/myapp/ios/App/App/Info.plist: default plist missing the four NS*UsageDescription keys
