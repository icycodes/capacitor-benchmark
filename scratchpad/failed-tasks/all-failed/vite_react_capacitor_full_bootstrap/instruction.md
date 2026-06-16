# Bootstrap a Vite + React + TypeScript App as a Capacitor v8 Android Project

## Background
You have an empty workspace at `/home/user/workspace`. Your team wants to start a brand-new mobile-ready web app: a fresh Vite + React + TypeScript SPA wrapped with Capacitor v8 and prepared for Android. The whole pipeline must be reproducible non-interactively from the command line so that it can run inside CI.

Nothing has been scaffolded yet. You are responsible for creating the project from scratch, wiring up Capacitor, generating the native Android project, configuring the bundler so that the WebView can actually load the compiled assets, and producing a fully synced native build.

## Requirements
- Use the official Vite scaffolder to create a fresh React + TypeScript project named `myapp` at `/home/user/workspace/myapp` (the resulting `package.json` must declare both `react` and `react-dom` runtime dependencies plus `typescript` and `vite` dev dependencies).
- Inside the `myapp` project, install the Capacitor v8 packages `@capacitor/core`, `@capacitor/cli`, and `@capacitor/android` (all major version 8.x).
- Initialize Capacitor non-interactively with the human-readable app name `My App`, the bundle id `com.example.myapp`, and the web directory `dist`.
- Add the Android platform to the project so that a native Android source tree appears under `myapp/android`.
- Configure Vite so that relative asset URLs are emitted into the built `index.html` (i.e. `base: './'` in `vite.config.ts`); without this, the Android WebView cannot resolve `/assets/*.js` references when serving the bundle from the local `file://` / `https://localhost` origin.
- Produce a successful production web build (`npm run build`) and copy the output into the native Android project with `npx cap sync android` so that the WebView assets land under `android/app/src/main/assets/public/`.

## Implementation Hints
- Refer to the official "cap init" CLI reference and the Capacitor v8 environment setup docs for the exact non-interactive invocation.
- `npm create vite@latest <name> -- --template react-ts` will scaffold the SPA without prompting once the template flag is supplied.
- The Capacitor CLI prints prompts when called without arguments; pass the app name, app ID, and `--web-dir` directly so it runs unattended.
- Vite's `base` option controls the public path baked into the built HTML. The default (`/`) produces absolute `/assets/...` URLs that break inside the Android WebView; switch it to `'./'` so the emitted paths are relative to `index.html`.
- `npx cap sync android` runs `cap copy` and `cap update`. It will refuse to run until the web bundle exists, so always run `npm run build` first.
- The Android SDK, JDK, Node.js 22, and a pre-warmed Gradle/npm cache are already provisioned in the environment. Working offline-friendly is fine but not required.

## Acceptance Criteria
- Project path: `/home/user/workspace/myapp`
- `package.json` at `/home/user/workspace/myapp/package.json` must:
  - List `react` and `react-dom` under `dependencies`.
  - List `typescript` and `vite` under `devDependencies`.
  - List `@capacitor/core` and `@capacitor/android` (both `^8` or `8.x`) under `dependencies`.
  - List `@capacitor/cli` (`^8` or `8.x`) under `devDependencies`.
- A Vite config file (`vite.config.ts` or `vite.config.js`) must exist at the project root and contain a top-level `base` option set to the relative string `'./'` (single or double quotes acceptable).
- A Capacitor config file (`capacitor.config.ts`, `capacitor.config.js`, or `capacitor.config.json`) must exist at the project root and declare:
  - `appId` equal to `com.example.myapp`.
  - `appName` equal to `My App`.
  - `webDir` equal to `dist`.
- The native Android project must exist at `/home/user/workspace/myapp/android` with the standard Gradle layout (`android/build.gradle`, `android/app/build.gradle`, `android/settings.gradle`, `android/gradlew`).
- The synced web bundle must be present at `/home/user/workspace/myapp/android/app/src/main/assets/public/index.html` (this is what `npx cap sync android` writes after `npm run build`).
- The `dist/index.html` produced by `npm run build` must reference its JS/CSS bundles using relative URLs (paths starting with `./assets/` rather than absolute `/assets/`).

