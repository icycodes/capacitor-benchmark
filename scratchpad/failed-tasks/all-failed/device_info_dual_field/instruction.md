# Render Platform, OS Version, and Language Code with Capacitor Device Plugin

## Background
A Vite + TypeScript web application has already been scaffolded at `/home/user/myapp`. The `@capacitor/device` plugin (v8.x) exposes a JavaScript API that returns information about the running device. On the web target, `Device.getInfo()` resolves to an object whose `platform` is `"web"` and whose `osVersion` is a version-like string derived from the user agent. `Device.getLanguageCode()` resolves to an object whose `value` is a two-character language code derived from `navigator.language` (for example, `"en"` when the browser is launched with `--lang=en-US`).

The pre-scaffolded project does NOT include Capacitor yet. Your job is to integrate Capacitor v8, install the Device plugin, and wire up two distinct pieces of UI: a section that always shows the platform and OS version on page load, and a button that fetches and renders the language code on demand.

## Requirements
- Integrate Capacitor v8 into the existing Vite project using the non-interactive CLI flow. The Capacitor app must be configured with:
  - App name: `Device Info Dual`
  - Application/package id: `com.example.deviceinfodual`
  - Web assets directory aligned with Vite's build output (`dist`).
- Add `@capacitor/device` to the project dependencies with a `major === 8` version (for example, `^8.0.0`).
- On page load, call `Device.getInfo()` and render its `platform` and `osVersion` values into the page.
  - `#device-platform` text content must equal the live `platform` value (the web fallback returns `"web"`).
  - `#device-os-version` text content must equal the live `osVersion` value (a non-empty, version-like string starting with a digit, e.g. `"10.15.7"` or `"118.0"`).
- Add a button with id `lang-btn`. When clicked, the handler must call `Device.getLanguageCode()` and put the returned `value` into the text content of `<span id="device-lang">`.
- `npx cap sync` must run successfully against the produced web build.

## Implementation Hints
- Use `npx cap init` with positional `appName` and `appId` arguments and the `--web-dir` flag to avoid the interactive prompt.
- Import `Device` from `@capacitor/device` and `await` the API calls before mutating the DOM.
- Vite's default build output directory is `dist`, which must match `webDir` in the Capacitor config.
- The Device plugin works on the web target without any native runtime, so the production preview server is sufficient for verification.
- The script that wires up the values must be loaded as an ES module so that the dynamic import of `@capacitor/device` succeeds.
- The language code is fetched lazily: the `#device-lang` span should be empty (or a placeholder) until the user clicks `#lang-btn`.

## Acceptance Criteria
- Project path: /home/user/myapp
- Start command: `npm run preview -- --host 0.0.0.0 --port 4173`
- Port: 4173
- `npm run build` must complete without errors and produce a `dist/` directory containing `index.html`.
- A Capacitor config file (`capacitor.config.ts`, `capacitor.config.js`, or `capacitor.config.json`) must exist at the project root with `appName` equal to `Device Info Dual`, `appId` equal to `com.example.deviceinfodual`, and `webDir` equal to `dist`.
- `package.json` must list `@capacitor/core`, `@capacitor/cli`, and `@capacitor/device` as dependencies (any of `dependencies` or `devDependencies`). The installed `@capacitor/device` version must have major version `8`.
- `npx cap sync` executed after the production build must exit with status 0.
- Routes / UI:
  - The page served at `http://localhost:4173/` must render an element with id `device-platform`, an element with id `device-os-version`, a `<button>` with id `lang-btn`, and a `<span>` with id `device-lang`.
  - After the page loads in a Chromium-based browser:
    - `#device-platform` text content equals `web`.
    - `#device-os-version` text content is non-empty and matches the regular expression `^[0-9].*` (a version-like string starting with a digit).
  - After the user clicks `#lang-btn`:
    - `#device-lang` text content matches the regular expression `^[a-z]{2}(-[A-Z]{2})?$`. When the browser is launched with `--lang=en-US`, the text content must contain `en`.

