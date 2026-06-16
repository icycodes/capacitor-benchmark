# Migrate from `cordova-plugin-device` to `@capacitor/device`

## Background
A hybrid mobile project located at `/home/user/myproject` currently uses the legacy `cordova-plugin-device` plugin (loaded via `cordova.js`) to obtain device metadata. Capacitor is already installed in the project, but the device reader still depends on the old Cordova plugin and the global `window.device` object. Your job is to migrate the project so that all device information is sourced from the official `@capacitor/device` plugin instead.

## Requirements
- Uninstall the Cordova device plugin from the project's npm dependencies (it must be removed from `package.json` / `package-lock.json` and from `node_modules`).
- Install the official `@capacitor/device` plugin and register it inside the Capacitor configuration so it is discoverable by `npx cap sync`.
- Remove every reference to `cordova.js` from `www/index.html` (the `<script src="cordova.js"></script>` tag must no longer exist).
- Remove every usage of the deprecated `window.device` global from the project source code (e.g. `www/js/device-info.js`). Nothing in the migrated source files may still reference `window.device` or `cordova.plugins.device`.
- Rewrite the device-info reader so that it uses the `@capacitor/device` plugin API, calling `Device.getInfo()`, `Device.getId()`, and `Device.getBatteryInfo()` via `async`/`await`.
- Expose the migrated reader as a Node-callable script that, when executed, prints a single JSON object on stdout combining the three API responses.
- Run `npx cap sync` after the migration and capture its output so the verifier can confirm the sync step completed successfully.

## Implementation Hints
- Look at the existing Cordova-based reader to understand which fields it exposes (uuid, model, platform, version, manufacturer, battery level, charging state) and map them to the modern Capacitor Device API equivalents.
- The `@capacitor/device` web implementation reads from `navigator`, so the Node command-line wrapper must set up a minimal `navigator`/`window` shim before importing the plugin so it can execute outside a real browser.
- Capacitor configuration lives in `capacitor.config.json` at the project root. Adjust it as needed (for example, remove obsolete Cordova-only preferences and make sure the project still validates) so that `npx cap sync` exits with code 0.
- The verifier will read both static project files and the recorded `npx cap sync` log, then re-run the migrated reader script. Make sure the script is idempotent and produces deterministic JSON keys.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Ensure the migration is actually performed and the artifacts below exist.
- Log file: `/home/user/myproject/sync.log` — must contain the full stdout/stderr of a successful `npx cap sync` run (the file must include the literal substring `sync finished` somewhere in its contents).
- `package.json` must NOT contain `cordova-plugin-device` in either `dependencies` or `devDependencies`, and must contain `@capacitor/device` in `dependencies`.
- `node_modules/@capacitor/device` must exist and `node_modules/cordova-plugin-device` must NOT exist after migration.
- `www/index.html` must NOT contain the substring `cordova.js`.
- No file under `www/` may contain the substrings `window.device` or `cordova.plugins.device` (search is case-sensitive).
- The migrated reader module must be invokable as `node /home/user/myproject/scripts/device-report.mjs` (or the equivalent CommonJS `.js`). When invoked, it must print exactly one line of JSON to stdout that, when parsed, satisfies the following shape:
  ```json
  {
    "info": { "platform": string, "operatingSystem": string, "osVersion": string, "manufacturer": string, "model": string, "isVirtual": boolean, "webViewVersion": string },
    "id": { "identifier": string },
    "battery": { "batteryLevel": number, "isCharging": boolean }
  }
  ```
  All listed fields must be present (the `info.platform` value will be `"web"` when running under Node).
- The reader source must import the `Device` symbol from `@capacitor/device` (verifier searches for the literal `from '@capacitor/device'` or `require('@capacitor/device')`) and must call all three of `Device.getInfo`, `Device.getId`, and `Device.getBatteryInfo`.
- `npx cap sync` must exit with status 0 when re-run by the verifier inside the project directory.

