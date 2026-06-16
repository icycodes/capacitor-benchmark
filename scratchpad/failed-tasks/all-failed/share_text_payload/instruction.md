# Install @capacitor/share v8 and Wire a Share Button to a Text Payload

## Background
[`@capacitor/share`](https://capacitorjs.com/docs/apis/share) is the official Capacitor v8 plugin that exposes the native share sheet on iOS and Android while transparently falling back to the browser's [Web Share API](https://web.dev/web-share/) (`navigator.share`) on the Web platform. Because the Web fallback drives the browser-native dialog, you can wire and verify the integration entirely in a headless Linux environment by intercepting `navigator.share` from the test runtime.

A Vite + TypeScript project is pre-scaffolded at `/home/user/myapp` and already contains a working Capacitor v8 setup (`@capacitor/core` and `@capacitor/cli` installed; `capacitor.config.ts` present). However it does NOT depend on `@capacitor/share` yet, and the served `index.html` does not contain any share button. Your task is to install the v8 plugin, render a `<button id="share-btn">` on the page, and wire its click handler to call `Share.share` with the exact payload `{ title: "Demo", text: "Hello from Capacitor", dialogTitle: "Choose" }`.

## Requirements
- Add `@capacitor/share` to the project's `dependencies` at the v8 major version (`^8.x.x` or any specifier that resolves to a v8 release).
- Ensure the page served by the Vite preview server renders a button with `id="share-btn"` (you may add it to `index.html`, inject it from `src/main.ts`, or any other approach as long as the rendered DOM exposes the button).
- When the button is clicked, the page must invoke `Share.share({ title: "Demo", text: "Hello from Capacitor", dialogTitle: "Choose" })` from the `@capacitor/share` plugin exactly once per click.
- After your changes, `npm run build` must exit with code 0 and emit `/home/user/myapp/dist/index.html`, and `npx cap sync` must exit with code 0.

## Implementation Hints
- Install the plugin and re-sync the native projects after installation: see https://capacitorjs.com/docs/apis/share for the full v8 reference.
- On the Web platform the plugin's `share()` method ultimately calls `navigator.share(...)`. You do not need to add any platform check — the test harness installs a stub for `navigator.share` before clicking the button, so the call will resolve cleanly even in headless Chromium.
- The existing `src/main.ts` is already loaded from `index.html`, which makes it a convenient place to import `Share` from `@capacitor/share` and attach a click handler that calls `Share.share(...)`.
- The payload object passed to `Share.share` must contain `title`, `text`, and `dialogTitle` with the exact string values listed in the Requirements. Keep them in a single `share()` invocation.

## Acceptance Criteria
- Project path: /home/user/myapp
- Start command: `npm run preview -- --host 0.0.0.0 --port 4173`
- Port: 4173
- `/home/user/myapp/package.json` declares `@capacitor/share` in `dependencies` with a version whose resolved semver major equals `8`.
- `npm run build` exits with status 0 and produces `/home/user/myapp/dist/index.html`.
- `npx cap sync` exits with status 0.
- HTTP GET `http://localhost:4173/` returns status 200 and the served HTML response body contains a `<button>` element with `id="share-btn"` (the button may also be injected from the entry script — the verifier checks the rendered DOM after the page has loaded).
- In a headless Chromium context where `navigator.share` is replaced by a stub that pushes every argument into `window.__shareCalls`, clicking the `#share-btn` button results in exactly one entry in `window.__shareCalls`, and that entry has `title === "Demo"` AND `text === "Hello from Capacitor"`.

