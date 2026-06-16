# Install and Configure the Capacitor SplashScreen Plugin

## Background
Capacitor v8 splits its functionality across small, official plugin packages. The `@capacitor/splash-screen` plugin controls the native launch splash screen on iOS and Android and exposes a small JavaScript API (`SplashScreen.show()` / `SplashScreen.hide()`). Its launch-time appearance is configured through the `plugins.SplashScreen` block of the Capacitor configuration file (`capacitor.config.ts` / `capacitor.config.json`).

A Vite + TypeScript project has been pre-scaffolded at `/home/user/myapp`. Capacitor v8 core and CLI are already installed and a `capacitor.config.ts` exists at the project root, but the SplashScreen plugin is NOT installed and the entry module does not yet call `SplashScreen.hide()`. Your job is to install the v8 splash-screen plugin, configure its launch options through the existing Capacitor config, and call `SplashScreen.hide()` from the TypeScript entry module after the DOM is ready.

## Requirements
- Install `@capacitor/splash-screen` at major version `8.x` as a runtime dependency in `/home/user/myapp/package.json`.
- Extend the existing Capacitor config at the project root so the `plugins.SplashScreen` block contains EXACTLY these option values (option names must match the v8 plugin spec exactly):
    - `launchShowDuration`: `3000`
    - `backgroundColor`: `"#ffffffff"`
    - `showSpinner`: `true`
    - `androidSpinnerStyle`: `"large"`
    - `iosSpinnerStyle`: `"small"`
  The resulting configuration is evaluated with `npx tsx` so both `.ts` and `.json` formats are accepted.
- Update a TypeScript source file under `/home/user/myapp/src/` so that:
    - It imports `SplashScreen` from `@capacitor/splash-screen`.
    - It calls `SplashScreen.hide()` once the DOM is ready (e.g., wrapped in a `DOMContentLoaded` listener or scheduled from the entry module that the bundled HTML loads).
- `npm run build` must continue to exit `0` and produce `dist/index.html`.
- `npx cap sync` must continue to exit `0`.

## Implementation Hints
- The plugin is published on npm as `@capacitor/splash-screen`. Install it explicitly at the v8 major (`npm install @capacitor/splash-screen@^8`) so that `package.json` records a `^8.x` range.
- All five required options are documented in the official Capacitor SplashScreen plugin reference. The exact option names matter; do not rename or alias them.
- The Capacitor v8 config supports a top-level `plugins` key with per-plugin sub-objects keyed by plugin display name (`SplashScreen`).
- `SplashScreen.hide()` is asynchronous; you can `await` it inside an async function or chain `.catch(...)` to swallow rejections during local dev.
- You do not need to write any new HTML markup; just make sure the entry TypeScript module that `index.html` loads actually executes the import and `SplashScreen.hide()` call.

## Acceptance Criteria
- Project path: /home/user/myapp
- Command: `npm run build` (run from the project path) must exit with status `0` and produce `dist/index.html`.
- Command: `npx cap sync` (run from the project path) must exit with status `0`.
- `package.json` must list `@capacitor/splash-screen` in `dependencies` with a version whose resolved major is exactly `8`.
- The Capacitor config file at the project root (`capacitor.config.ts` or `capacitor.config.json`) must define a `plugins.SplashScreen` object containing exactly the option values listed under Requirements. The verifier evaluates the config via `npx tsx` so both TypeScript and JSON config forms are supported.
- At least one TypeScript source file under `/home/user/myapp/src/` must contain BOTH an import from `@capacitor/splash-screen` AND a `SplashScreen.hide()` call. The verifier uses regex-tolerant matching across the import statement and the method invocation.

