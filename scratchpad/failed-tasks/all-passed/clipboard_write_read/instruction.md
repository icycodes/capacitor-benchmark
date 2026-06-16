# Copy and Paste Text with the Capacitor Clipboard Plugin

## Background
You are extending a small Vite + TypeScript web application that will eventually be packaged as a native mobile app via Capacitor v8. The `@capacitor/clipboard` plugin exposes a unified API for writing to and reading from the system clipboard on iOS, Android, and Web. On the web target, the plugin delegates to the standard browser `navigator.clipboard` API, so the very same JavaScript code that runs on a mobile device also works inside the headless Chromium browser used by this task's verifier.

A minimal Vite + TypeScript project, with Capacitor v8 core/CLI already installed and configured, has been pre-scaffolded for you at `/home/user/myapp`. Your job is to install the Capacitor Clipboard plugin and wire up a tiny UI that copies the current value of a text input to the clipboard through `Clipboard.write` and pastes it back through `Clipboard.read`.

## Requirements
- Install `@capacitor/clipboard` at a version compatible with Capacitor v8 (i.e. major version `8`).
- Implement a UI in `index.html` (and any TypeScript modules under `src/`) that contains:
    - An `<input>` element with the HTML id `clip-input`.
    - A `<button>` element with the HTML id `clip-write-btn`.
    - A `<button>` element with the HTML id `clip-read-btn`.
    - A `<span>` element with the HTML id `clip-output` (its initial text content must be empty).
- Clicking `#clip-write-btn` must call `Clipboard.write({ string: <current value of #clip-input> })`. You may NOT shortcut the requirement by writing directly to `navigator.clipboard.writeText` or by storing the value in a local JavaScript variable / `localStorage` — the value MUST be copied to the system clipboard through the Capacitor Clipboard plugin.
- Clicking `#clip-read-btn` must call `Clipboard.read()` and write the returned `value` (a string) verbatim into the `textContent` of `#clip-output`.
- After installing the plugin, `npm run build` must succeed and `npx cap sync` must exit with status 0 against the produced web build (no native platforms need to be added).

## Implementation Hints
- The pre-scaffolded project already contains a working `capacitor.config.ts` with `webDir` set to `dist`, so you do not need to re-run `npx cap init`.
- Install the plugin with `npm install @capacitor/clipboard@^8`.
- Import `Clipboard` from `@capacitor/clipboard`.
- The `Clipboard.read()` method returns a `Promise<{ value: string; type: string }>`; only the `value` field needs to be displayed.
- Make sure the script that wires up the buttons is loaded as an ES module so that the import of `@capacitor/clipboard` resolves at runtime.
- Vite serves the build output via `npm run preview`. The default build output directory is `dist` and matches the pre-configured `webDir`.

## Acceptance Criteria
- Project path: /home/user/myapp
- Start command: `npm run preview -- --host 0.0.0.0 --port 4173 --strictPort`
- Port: 4173
- `package.json` must list `@capacitor/clipboard` with a version whose semver major is `8` in either `dependencies` or `devDependencies`.
- `npm run build` must complete without errors and produce `dist/index.html`.
- `npx cap sync` (executed after the production build) must exit with status 0.
- The served page at `http://localhost:4173/` must contain an `<input>` element with `id="clip-input"`, a `<button>` element with `id="clip-write-btn"`, a `<button>` element with `id="clip-read-btn"`, and a `<span>` element with `id="clip-output"`.
- Browser behaviour (headless Chromium with clipboard permissions granted):
    - Filling `#clip-input` with `benchmark text` and clicking `#clip-write-btn` must copy the string to the system clipboard via the Capacitor Clipboard plugin.
    - Clicking `#clip-read-btn` afterwards must populate `#clip-output` with text content exactly equal to `benchmark text`.
    - Reading the underlying browser clipboard with `navigator.clipboard.readText()` after the write must also return `benchmark text` (this proves the plugin actually wrote to the system clipboard, not to a local variable).

