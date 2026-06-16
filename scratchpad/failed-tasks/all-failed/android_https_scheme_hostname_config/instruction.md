# Configure Capacitor Android `https` Scheme with a Custom Hostname

## Background
A pre-bootstrapped Capacitor v8 project is provided at `/home/user/myapp`. The team has been chasing an Android-only CORS issue: backend services keep rejecting requests because Chromium's WebView truncates non-standard custom schemes on Android (sending `app://` without the `localhost` host part), even though the same backends work on iOS. The fix is to switch Android over to a standard `https` scheme and a custom hostname so the origin is consistent, while still letting local debug traffic to `localhost` work over cleartext.

Your job is to reconfigure the project so the Android WebView serves the app from `https://myapp.example.com` and to update Android's Network Security Configuration so plain `http://localhost` traffic remains permitted while `myapp.example.com` stays TLS-only. After making the configuration changes you must run `npx cap sync android` cleanly so the new configuration propagates into the native Android project.

The project is fully scaffolded already (web assets built into `dist/`, `@capacitor/android` installed, `android/` platform added). Do not regenerate or re-add the platform; modify the existing files in place.

## Requirements
- Update `capacitor.config.ts` so the Capacitor `server` configuration sets `androidScheme` to `https` and `hostname` to `myapp.example.com`. Existing top-level fields (`appId`, `appName`, `webDir`) must be preserved.
- Create (or overwrite) `android/app/src/main/res/xml/network_security_config.xml` so that cleartext HTTP traffic is permitted **only** for the `localhost` domain, while the rest of the app (including `myapp.example.com`) keeps the platform default of HTTPS-only.
- Wire the network security configuration into `android/app/src/main/AndroidManifest.xml` by setting `android:networkSecurityConfig="@xml/network_security_config"` on the `<application>` element. Leave the rest of the manifest untouched.
- Run `npx cap sync android` so the modified configuration is synced into the native Android project. The command must complete with a zero exit code.

## Implementation Hints
- The Capacitor configuration is a TypeScript module that exports a typed `CapacitorConfig` object — keep the export shape and add the `server` block alongside the existing top-level fields.
- Android's Network Security Configuration uses `<domain-config cleartextTrafficPermitted="true">` with one or more nested `<domain includeSubdomains="false">` elements to restrict cleartext to specific hosts. The platform default for everything else is HTTPS-only, so you do not need to add a `<base-config>` block.
- The Android manifest reference uses the `android:networkSecurityConfig` attribute on the `<application>` tag and resolves against `res/xml/<name>.xml` resources.
- `npx cap sync android` will re-run Capacitor's configuration emitter; failures from this command usually point at a malformed `capacitor.config.ts` or a missing native platform.

## Acceptance Criteria
- Project path: /home/user/myapp
- Ensure the configuration changes are applied and `npx cap sync android` is executed against the real project.
- Sync log file: /home/user/myapp/sync.log — must capture stdout+stderr of the final `npx cap sync android` invocation and end with that command exiting `0`.
- `capacitor.config.ts` must export a `CapacitorConfig` where:
  - `server.androidScheme` is the string `https`.
  - `server.hostname` is the string `myapp.example.com`.
  - The original `appId`, `appName`, and `webDir` values are preserved.
- `android/app/src/main/res/xml/network_security_config.xml` must exist and:
  - Declare a `<network-security-config>` root element.
  - Permit cleartext traffic for the `localhost` domain (a `<domain-config>` with `cleartextTrafficPermitted="true"` that contains a `<domain>` whose text is exactly `localhost`).
  - Not declare a global `<base-config cleartextTrafficPermitted="true">` (cleartext must NOT be a global default).
- `android/app/src/main/AndroidManifest.xml` must:
  - Contain an `<application>` element with `android:networkSecurityConfig="@xml/network_security_config"`.
  - Keep all other elements and attributes (such as `android:allowBackup`, `android:label`, activities, intent filters) intact.

