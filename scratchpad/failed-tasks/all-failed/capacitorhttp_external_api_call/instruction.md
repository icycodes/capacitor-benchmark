# Render a List from an External JSON API via CapacitorHttp

## Background
Capacitor v8 ships a built-in `CapacitorHttp` plugin as part of `@capacitor/core`. When enabled in the Capacitor configuration file (`plugins.CapacitorHttp.enabled = true`), it patches `window.fetch` / `XMLHttpRequest` and exposes explicit `CapacitorHttp.get`/`post` methods that route HTTP traffic through native HTTP clients on iOS and Android. This makes it the recommended escape hatch for the CORS friction documented in the Capacitor + Ionic troubleshooting guide: requests originating from `capacitor://localhost` or `http://localhost` are not allowed by most third-party APIs unless the request goes through the native HTTP layer.

A Vite + TypeScript project has already been scaffolded at `/home/user/myapp` with Capacitor v8 installed and a `capacitor.config.ts` at the project root. The plugin is **not yet enabled** and the page does not yet perform any network requests. Your job is to enable `CapacitorHttp`, build a small UI that fetches a JSON document from a URL injected at runtime, and render every item in the response into a list on the page. The test fixture hosts a CORS-restricted JSON endpoint and uses Playwright to drive the UI end-to-end, so a fully working `CapacitorHttp.get` integration is required.

## Requirements
- Enable the `CapacitorHttp` plugin via the existing `capacitor.config.ts` so that the resulting Capacitor configuration has `plugins.CapacitorHttp.enabled === true`. The configuration must remain a valid Capacitor v8 `CapacitorConfig` literal.
- After modifying the config, `npm run build` and `npx cap sync` must continue to succeed.
- Render a small UI in the existing Vite app that contains, at minimum:
  - A `<button>` element with the HTML id `fetch-btn`.
  - A `<ul>` element with the HTML id `items`. Its initial children list may be empty, but it must be populated when the user clicks the button.
- When the button is clicked, the page must:
  1. Read the target URL from `window.__API_URL__` (the test fixture injects this value via Playwright's `addInitScript` before the page navigates). You may assume the value is a non-empty string.
  2. Call `CapacitorHttp.get({ url: window.__API_URL__ })` (imported from `@capacitor/core`) and `await` the result.
  3. Parse the JSON response body to obtain `response.data.items`, which is an array of objects of shape `{ name: string }`.
  4. Render each entry as an `<li>` element whose text content is the `name` field, appended in the same order as the array, into `#items`. After a successful click, `#items` must contain exactly N `<li>` children, where N is the length of `response.data.items`.
- The implementation MUST use `CapacitorHttp.get` from `@capacitor/core`. Using only the global `fetch`/`XMLHttpRequest` without going through `CapacitorHttp` is not acceptable, because the verifier ships a JSON endpoint whose `Access-Control-Allow-Origin` does not match the Vite preview origin.

## Implementation Hints
- `CapacitorHttp` is a property of `@capacitor/core`'s default export and does not require an additional `npm install`. Import it with `import { CapacitorHttp } from '@capacitor/core';`.
- To enable the plugin in TypeScript config, add a top-level `plugins` key to the `CapacitorConfig` literal:
  ```ts
  const config: CapacitorConfig = {
    // ...existing fields
    plugins: {
      CapacitorHttp: { enabled: true },
    },
  };
  ```
- The mock server returns a JSON body with `Content-Type: application/json`, so `CapacitorHttp` will auto-parse it; `response.data` is the parsed object, not a string.
- Read `window.__API_URL__` inside the click handler so that the value injected by the test is available at request time.
- The button and list must be present in the served HTML by the time Playwright clicks `#fetch-btn` (either in `index.html` directly or rendered before the click). The verifier uses Playwright's `wait_for_selector`, so a small render delay is acceptable.

## Acceptance Criteria
- Project path: /home/user/myapp
- Start command: `npm run preview -- --host 0.0.0.0 --port 4173`
- Port: 4173
- The Capacitor config file at the project root (either `capacitor.config.ts` or `capacitor.config.json`) must enable `CapacitorHttp` such that the resulting configuration satisfies `plugins.CapacitorHttp.enabled === true`. A regex-tolerant check accepts both `.ts` and `.json` representations.
- `npm run build` exits with status 0 and produces `dist/index.html`.
- `npx cap sync` exits with status 0.
- The page served at `http://127.0.0.1:4173/` contains an element matching `<button id="fetch-btn">` and an element matching `<ul id="items">`.
- After Playwright launches headless Chromium, injects a URL pointing at a local Python `http.server` into `window.__API_URL__`, navigates to `http://127.0.0.1:4173/`, and clicks `#fetch-btn`, the `#items` element must contain exactly three `<li>` children whose `textContent` values, in order, equal `["Apple", "Banana", "Cherry"]` within a 10-second timeout.

