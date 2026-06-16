# Background-Aware Geolocation Tracker with Capacitor App + Geolocation + Preferences

## Background
You are extending a Vite + TypeScript application that is already wired up as a Capacitor v8 project. The team needs a self-contained tracking module that continuously samples device coordinates while the app is in the foreground but stops recording the moment the operating system moves the app to the background, then transparently resumes when the user comes back. The latest known position must outlive a hard relaunch so the UI can render something useful on cold start before a fresh GPS fix arrives.

On iOS and Android these lifecycle transitions come from the native `@capacitor/app` plugin. In a headless browser they come from the web implementation of `@capacitor/app`, which is wired to the document's `visibilitychange` event and reports `{ isActive: !document.hidden }`. Similarly, the web implementation of `@capacitor/geolocation` delegates to `window.navigator.geolocation.watchPosition` / `clearWatch`, so the entire feature can be exercised end-to-end in headless Chromium against the production preview build.

A Vite + TypeScript project is pre-scaffolded at `/home/user/myapp`. Capacitor v8 (core + CLI) is already installed and `capacitor.config.ts` is already in place (`appName: "Tracker App"`, `appId: "com.example.tracker"`, `webDir: "dist"`). The project does NOT yet depend on `@capacitor/app`, `@capacitor/geolocation`, or `@capacitor/preferences`, and the page does not yet expose the tracker. Your job is to install the three plugins (all at the v8 major), implement the tracker, and expose it on `window.tracker` so the verifier can drive it.

## Requirements
- Add `@capacitor/app`, `@capacitor/geolocation`, and `@capacitor/preferences` to the project's `dependencies` at the v8 major version (any specifier whose resolved semver major equals `8`).
- Implement the tracking module in TypeScript under `/home/user/myapp/src/`. You may use the pre-existing `src/main.ts` entry (already referenced from `index.html`) or split the implementation across additional modules; the only hard requirement is that the entry script wires the tracker onto the global `window` so the running page can use it.
- Expose a singleton tracker object globally as `window.tracker` with three async methods:
    - `start(): Promise<void>` — starts watching positions via `Geolocation.watchPosition(...)` and registers an `App.addListener('appStateChange', ...)` subscription so background transitions pause the watch and foreground transitions resume it. Calling `start()` while already started must be a no-op (do NOT create a second watch).
    - `stop(): Promise<void>` — clears the active `watchPosition` (if any) and removes the `appStateChange` listener so no further updates are recorded. Calling `stop()` while already stopped must be a no-op.
    - `getLatest(): Promise<{ lat: number; lng: number; timestamp: number } | null>` — resolves with the most recently observed position, or `null` if no position has ever been observed and nothing has been persisted yet. On cold start (fresh JS context after a full page reload) `getLatest()` must be callable BEFORE `start()` and must return the position that was persisted via `@capacitor/preferences` in the previous session.
- Whenever `Geolocation.watchPosition` invokes the callback with a new `Position`, the tracker must:
    1. Update its in-memory "latest" cache to `{ lat: position.coords.latitude, lng: position.coords.longitude, timestamp: position.timestamp }`.
    2. Persist that same object as a JSON string via `Preferences.set({ key: 'last_position', value: <json> })`.
- Background / foreground behavior driven by `App.addListener('appStateChange', ({ isActive }) => ...)`:
    - On `isActive === false` (background): `clearWatch` the active `watchPosition` and stop accepting position updates. The in-memory latest must be preserved (it must NOT be reset to `null`).
    - On `isActive === true` (foreground): if the tracker was previously started, start a NEW `watchPosition` so updates resume. Do NOT start a new watch if `stop()` has been called.
- The implementation must compile and bundle cleanly: `npm run build` must continue to exit 0 and produce `dist/index.html`, and `npx cap sync` must continue to exit 0.

## Implementation Hints
- Install the three plugins with one or more `npm install @capacitor/<plugin>@^8` invocations and run `npx cap sync` afterwards as recommended in the Capacitor docs.
- The web implementation of `@capacitor/geolocation` ultimately calls `window.navigator.geolocation.watchPosition`, so any feature you build on top of `Geolocation.watchPosition` works against the standard browser API — no native runtime is required for verification.
- The web implementation of `@capacitor/app` translates `document.visibilitychange` events into `appStateChange` events with `{ isActive: !document.hidden }`. Subscribing to `appStateChange` is therefore sufficient — you do not need to listen to `visibilitychange` directly.
- Because `Preferences.set` is async, take care that subsequent `getLatest()` calls observe the most recent value even when they are issued shortly after a position event.
- The verifier reaches into the running page via `window.tracker.start()`, `window.tracker.stop()`, and `window.tracker.getLatest()`. Make sure those bindings exist as soon as the entry script has finished initial evaluation. Loading the in-memory cache from Preferences during initialization is the most reliable way to make `getLatest()` cold-start friendly.
- Treat `start()` and `stop()` as idempotent state transitions; the verifier explicitly invokes them more than once.

## Acceptance Criteria
- Project path: /home/user/myapp
- Start command: `npm run preview -- --host 0.0.0.0 --port 4173`
- Port: 4173
- `/home/user/myapp/package.json` lists `@capacitor/app`, `@capacitor/geolocation`, and `@capacitor/preferences` under `dependencies`. The resolved semver major of each (read from `node_modules/@capacitor/<plugin>/package.json` if installed) must equal `8`.
- `npm run build` exits with status 0 and produces `/home/user/myapp/dist/index.html`.
- `npx cap sync` exits with status 0.
- When the Vite preview server is running and `http://localhost:4173/` is opened in a headless Chromium browser whose `navigator.geolocation` has been mocked BEFORE page scripts evaluate:
    - `window.tracker` exists and exposes `start`, `stop`, and `getLatest` (all returning Promises).
    - Before `start()` has ever been invoked AND with empty `localStorage`, `await window.tracker.getLatest()` resolves to `null`.
    - After calling `await window.tracker.start()`, exactly one geolocation watch is registered with the browser.
    - Simulating a position update on the mock causes `await window.tracker.getLatest()` to resolve to an object whose `lat`, `lng`, and `timestamp` numbers equal the emitted coordinates.
    - Persistence: `localStorage.getItem('CapacitorStorage.last_position')` becomes a non-empty string (the JSON the tracker stored via `Preferences.set`).
    - Dispatching a `visibilitychange` event with `document.hidden = true` clears the active geolocation watch (zero registered watches afterwards) and additional emitted positions are ignored (`getLatest()` keeps returning the last pre-background position).
    - Dispatching a `visibilitychange` event with `document.hidden = false` registers a new geolocation watch (exactly one active again) and a subsequent position emit is reflected in `getLatest()`.
    - After a full `page.reload()` (which preserves `localStorage`), `await window.tracker.getLatest()` resolves to the last position observed before the reload — without calling `start()` first.
    - After calling `await window.tracker.stop()`, no geolocation watches remain registered and additional dispatched `visibilitychange` events do NOT register a new watch.

