# Install @capacitor/app v8 and Render Live App Active/Inactive State

## Background
[`@capacitor/app`](https://capacitorjs.com/docs/apis/app) is the official Capacitor v8 plugin that exposes high-level application lifecycle events (foreground/background, deep links, back button, etc.). On the web, the plugin's `appStateChange` event is wired to the document's `visibilitychange` event, so an `appStateChange` listener receives `{ isActive: true }` when `document.hidden === false` and `{ isActive: false }` when `document.hidden === true`. That makes the plugin verifiable in a headless Chromium browser without any native build.

A Vite + TypeScript project pre-scaffolded with Capacitor v8 already exists at `/home/user/myapp`. The project builds and syncs cleanly, but it does NOT yet depend on `@capacitor/app` and the page does not contain the `#app-state` element. Your task is to install the `@capacitor/app` plugin at the v8 major version, add `<span id="app-state">` to the page, and wire the `appStateChange` listener so that the span always reflects the live active/inactive state.

## Requirements
- Add `@capacitor/app` to the project's `dependencies` at the v8 major version (`^8.x.x` or any specifier that resolves to a v8 release).
- Add a `<span id="app-state">` element to the page (you may edit `index.html` directly, or create it from TypeScript before the listener fires). Its initial visible `textContent` on page load **must** be `"active"`.
- Edit a TypeScript file under `/home/user/myapp/src/` (you may use the pre-existing `src/main.ts` entry, which is already loaded by `index.html`) so that it:
    - Imports `App` from `@capacitor/app`.
    - Subscribes via `App.addListener('appStateChange', ({ isActive }) => ...)`.
    - In the listener, writes `"active"` to `#app-state.textContent` when `isActive === true`, otherwise writes `"inactive"`.
- After your changes, `npm run build` and `npx cap sync` must still both exit with code 0, and the production build at `dist/index.html` must exist.

## Implementation Hints
- The plugin can be installed with `npm install @capacitor/app@^8`. The Capacitor docs (https://capacitorjs.com/docs/apis/app) recommend running `npx cap sync` after installation to register the plugin with the native platforms.
- The web implementation of `appStateChange` is implemented on top of `document.visibilitychange` and reports `isActive: !document.hidden`. Toggling `document.hidden` and firing a `visibilitychange` event therefore drives the listener end-to-end in a headless browser.
- The initial `textContent` of `#app-state` must be `"active"` before any visibility change fires, because the verifier reads it immediately on page load.
- Make sure the `App.addListener(...)` call is reachable from the page's entry script so Vite does not tree-shake it away. The pre-existing `src/main.ts` is already referenced from `index.html`, which makes it the simplest place to add the integration.

## Acceptance Criteria
- Project path: /home/user/myapp
- Start command: `npm run preview -- --host 0.0.0.0 --port 4173`
- Port: 4173
- `/home/user/myapp/package.json` declares `@capacitor/app` in `dependencies` with a version whose resolved semver major equals `8`.
- `npm run build` exits with status 0 and produces `/home/user/myapp/dist/index.html`.
- `npx cap sync` exits with status 0.
- When the Vite preview server is started and `http://localhost:4173/` is opened in a headless Chromium browser:
    - On initial load, the element matched by CSS selector `#app-state` exists and its `textContent` equals `"active"`.
    - After running `await page.evaluate("Object.defineProperty(document, 'hidden', { value: true, configurable: true }); document.dispatchEvent(new Event('visibilitychange'))")`, `#app-state.textContent` becomes `"inactive"` within 5 seconds.
    - After running the inverse (`hidden: false`) and dispatching `visibilitychange` again, `#app-state.textContent` returns to `"active"` within 5 seconds.

