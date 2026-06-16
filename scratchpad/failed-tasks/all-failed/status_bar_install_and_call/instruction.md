# Install @capacitor/status-bar v8 and Configure the Status Bar on App Load

## Background
[`@capacitor/status-bar`](https://capacitorjs.com/docs/apis/status-bar) is the official Capacitor v8 plugin used to control the native status bar (text style, background color, visibility) on iOS and Android. On the web, the plugin is shipped as a thin no-op fallback, so the only way to verify correct integration in a headless Linux environment is to validate the wiring (dependency presence, source-level imports, calls that survive bundling) and ensure that `npm run build` and `npx cap sync` continue to succeed end-to-end.

A Vite + TypeScript project pre-scaffolded with Capacitor v8 already exists at `/home/user/myapp`. The project builds and syncs cleanly, but it does NOT yet depend on `@capacitor/status-bar` and never calls into the Status Bar API. Your task is to install the plugin from npm at the v8 major version, then add code in a TypeScript source file under `src/` that imports the `StatusBar` and `Style` symbols and calls both `StatusBar.setStyle({ style: Style.Dark })` and `StatusBar.setBackgroundColor({ color: '#222222' })` on app load.

## Requirements
- Add `@capacitor/status-bar` to the project's `dependencies` at the v8 major version (`^8.x.x` or any specifier that resolves to a v8 release).
- Edit a TypeScript file under `/home/user/myapp/src/` (you may use the pre-existing `src/main.ts` entry, which is already loaded by `index.html`) so that it:
    - Imports both `StatusBar` and `Style` from `@capacitor/status-bar`.
    - Calls `StatusBar.setStyle({ style: Style.Dark })` exactly once on module load (top-level or from a function invoked on load).
    - Calls `StatusBar.setBackgroundColor({ color: '#222222' })` exactly once on module load.
- The two `StatusBar` calls must appear verbatim (single OR double quotes accepted around `'#222222'`) in the TypeScript source so the verifier's regex check passes.
- After your changes, `npm run build` and `npx cap sync` must still both exit with code 0, and the production build at `dist/index.html` must exist.
- The compiled JS bundle that `dist/index.html` references must contain a substring matching the regex `setStyle.*Dark`, proving the call was preserved through Vite's tree-shaker.

## Implementation Hints
- The plugin can be installed with `npm install @capacitor/status-bar@^8`. The Capacitor CLI documentation (https://capacitorjs.com/docs/apis/status-bar) also recommends a `npx cap sync` after installation to register the plugin with the native platforms.
- The two relevant exports live on the package's default ESM entry: `import { StatusBar, Style } from '@capacitor/status-bar';`. The `Style` enum exposes members `Dark`, `Light`, and `Default` — you only need `Style.Dark` here.
- Even though Status Bar is a no-op on the web fallback, calling the methods unconditionally on app load is safe: the web implementation logs a warning and resolves the promise. You do not need to wrap the calls in any platform check.
- Make sure the calls are reachable from the page's entry script so Vite does not tree-shake them away. The pre-existing `src/main.ts` is already referenced from `index.html`, which makes it the simplest place to add the integration.

## Acceptance Criteria
- Project path: /home/user/myapp
- Start command: `npm run preview -- --host 0.0.0.0 --port 4173`
- Port: 4173
- `/home/user/myapp/package.json` declares `@capacitor/status-bar` in `dependencies` with a version whose resolved semver major equals `8`.
- At least one file matching `/home/user/myapp/src/**/*.{ts,tsx,js,mjs}` contains all of:
    - An `import` of both `StatusBar` and `Style` from `@capacitor/status-bar`.
    - A call matching `StatusBar.setStyle({ style: Style.Dark })`.
    - A call matching `StatusBar.setBackgroundColor({ color: '#222222' })` (single OR double quotes accepted).
- `npm run build` exits with status 0 and produces `/home/user/myapp/dist/index.html`.
- `npx cap sync` exits with status 0.
- HTTP GET on `http://localhost:4173/` returns status 200, and the JavaScript bundle referenced from the served HTML (e.g., `/assets/index-*.js`) contains a substring matching the regex `setStyle.*Dark`.

