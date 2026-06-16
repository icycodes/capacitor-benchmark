# Multi-Key Key/Value Admin UI with Capacitor Preferences

## Background
You are building a small Vite + TypeScript web application that will eventually be packaged as a native mobile app via Capacitor v8. Persistent settings must be stored using the `@capacitor/preferences` plugin instead of `window.localStorage`, because mobile operating systems may clear `localStorage` while the Preferences plugin uses durable native storage (with a `localStorage` fallback when the app runs as a Progressive Web App in the browser).

A minimal Vite TypeScript project has already been scaffolded for you at `/home/user/myapp`. Your job is to integrate Capacitor v8, install the Preferences plugin, and build a tiny key-value admin UI that exercises the full Preferences CRUD surface: `set`, `get`, `remove`, `clear`, and `keys`.

## Requirements
- Integrate Capacitor v8 into the existing Vite project using the non-interactive CLI flow. The Capacitor app must be configured with:
    - App name: `KV Admin`
    - Application/package id: `com.example.kvadmin`
    - Web assets directory aligned with Vite's build output (`dist`).
- Install and use the `@capacitor/preferences` plugin (version compatible with Capacitor v8) for ALL persistence. Do not call `window.localStorage` directly from your application code.
- Implement an admin UI in `index.html` that contains the following elements with these exact HTML ids:
    - `<input id="kv-key">` — text input for a key name.
    - `<input id="kv-value">` — text input for a value.
    - `<button id="kv-set-btn">Set</button>` — store the current key/value pair through `Preferences.set`.
    - `<button id="kv-remove-btn">Remove</button>` — remove the key currently in `#kv-key` through `Preferences.remove`.
    - `<button id="kv-clear-btn">Clear All</button>` — clear every stored key/value pair through `Preferences.clear`.
    - `<ul id="kv-list"></ul>` — a list that displays every stored key/value pair.
- The list must be refreshed automatically after every operation (`Set`, `Remove`, `Clear All`) AND on every page load by:
    1. Calling `Preferences.keys()` to enumerate the currently stored keys.
    2. Calling `Preferences.get({ key })` for each key.
    3. Rendering each pair as `<li data-key="<key>"><key>=<value></li>` inside `#kv-list`.
- The list ordering does not need to be sorted, but each key MUST appear exactly once.
- `npx cap sync` must run successfully against the produced web build.

## Implementation Hints
- Use `npx cap init` with positional `appName` and `appId` arguments and the `--web-dir` flag to avoid the interactive prompt.
- Import `Preferences` from `@capacitor/preferences` in your TypeScript code; the API methods you need are `Preferences.set({ key, value })`, `Preferences.get({ key })`, `Preferences.remove({ key })`, `Preferences.clear()`, and `Preferences.keys()`.
- Vite's default build output directory is `dist`, which must match `webDir` in `capacitor.config.ts` (or `.json`).
- The Preferences plugin transparently falls back to `localStorage` on the web target (it uses keys prefixed with `CapacitorStorage.`), so no native runtime is required for the web build used to verify the behavior.
- Make sure the script that wires up the UI is loaded as an ES module so that imports from `@capacitor/preferences` succeed.
- Re-render `#kv-list` from scratch each time (clear existing `<li>` children before appending new ones) so the list always reflects the current Preferences state.

## Acceptance Criteria
- Project path: /home/user/myapp
- Start command: `npm run preview -- --host 0.0.0.0 --port 4173`
- Port: 4173
- `npm run build` must complete without errors and produce a `dist/` directory containing `index.html`.
- `capacitor.config.ts` (or `capacitor.config.json`) must exist at the project root with `appName` equal to `KV Admin`, `appId` equal to `com.example.kvadmin`, and `webDir` equal to `dist`.
- `package.json` must list `@capacitor/core`, `@capacitor/cli`, and `@capacitor/preferences` as dependencies (any of `dependencies` or `devDependencies`). The installed major version of `@capacitor/preferences` must be `8`.
- `npx cap sync` executed after the production build must exit with status 0.
- The served page at `http://localhost:4173/` must contain elements with HTML ids `kv-key`, `kv-value`, `kv-set-btn`, `kv-remove-btn`, `kv-clear-btn`, and `kv-list`.
- On a fresh browser session (empty `localStorage`), `#kv-list` must initially contain zero `<li>` children.
- After entering a key in `#kv-key` and a value in `#kv-value` and clicking `#kv-set-btn`, a `<li data-key="<key>"><key>=<value></li>` element must appear inside `#kv-list`, and the value must be retrievable via `Preferences.get`.
- Stored entries must persist across full page reloads (the list rebuilds itself from Preferences on load).
- Clicking `#kv-remove-btn` while `#kv-key` holds a stored key must remove that key from `#kv-list` and from Preferences.
- Clicking `#kv-clear-btn` must remove every `<li>` from `#kv-list` and clear every entry from Preferences.

