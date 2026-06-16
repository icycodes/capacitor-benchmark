# Photo Gallery with Capacitor Camera, Filesystem, and Preferences

## Background
You are building a small Vite + TypeScript web application that will eventually be packaged as a native mobile app via Capacitor v8. The app is a minimal photo gallery: the user captures (or, on the web target, picks) a photo, the app persists the captured JPEG bytes into the device's data directory through `@capacitor/filesystem`, and a small JSON index of the saved photo paths is kept in `@capacitor/preferences` so the gallery survives reloads.

A minimal Vite + TypeScript project has already been scaffolded for you at `/home/user/myapp`. Capacitor and its plugins are NOT installed yet — you must install and wire them up. The verification environment runs the production build under `npm run preview` and exercises the gallery in a headless Chromium browser, where Capacitor's web-fallback implementations of these plugins are used (the Camera plugin falls back to an `<input type="file">` picker when `@ionic/pwa-elements` is not registered, the Filesystem plugin persists in IndexedDB under `Directory.Data`, and Preferences persists in IndexedDB).

## Requirements
- Integrate Capacitor v8 into the existing Vite project using the non-interactive CLI flow. The Capacitor app must be configured with:
    - App name: `Photo Gallery`
    - Application/package id: `com.example.photogallery`
    - Web assets directory aligned with Vite's build output (`dist`).
- Install and use `@capacitor/camera` (version 8.1.0 or newer — i.e. the version that exposes `takePhoto`), `@capacitor/filesystem`, and `@capacitor/preferences` (versions compatible with Capacitor v8). You may NOT shortcut the persistence requirements by writing files or the index directly to `localStorage`, `IndexedDB`, in-memory globals, or `window.fetch`-backed caches — every persisted byte and index update MUST go through the Capacitor plugin APIs.
- Create a TypeScript module (for example `src/gallery.ts`) that exports three async functions, all of which MUST be reachable from the served page on `window.gallery` so that automated tests can invoke them:
    - `capturePhoto(): Promise<string>` — invoke `Camera.takePhoto({ saveToGallery: false, includeMetadata: true })`, take the returned base64 image bytes (on Web, the full image is returned in `result.thumbnail`), write them through `Filesystem.writeFile` to `Directory.Data` at the path `photos/<isoTimestamp>.jpeg` (where `<isoTimestamp>` is the value of `new Date().toISOString()` at the moment of capture), append the freshly written path to the Preferences index, and resolve with that path.
    - `listPhotos(): Promise<string[]>` — return the current JSON-decoded array of stored photo paths from Preferences. If the key has never been written, resolve with an empty array `[]`.
    - `deletePhoto(path: string): Promise<void>` — remove the file from `Directory.Data` via `Filesystem.deleteFile`, then update the Preferences index so the deleted path is no longer present. The two side effects MUST both occur; if the file does not exist the index must still be updated.
- The index MUST be stored in `@capacitor/preferences` under the key `photo_index`, and the stored value MUST be a JSON-serialized array of strings (e.g. `"[\"photos/2026-01-02T03:04:05.678Z.jpeg\"]"`). The order of the array MUST reflect insertion order.
- The served `index.html` must contain a single visible button with the HTML id `capture-btn` that, when clicked, calls `window.gallery.capturePhoto()` and updates a status element with the HTML id `capture-status` (text content `idle`, `capturing`, `saved`, or `error: <message>`). The remaining `listPhotos` / `deletePhoto` behaviour is exercised programmatically by tests via `window.gallery.*`.
- `npx cap sync` must run successfully against the produced web build (no native platforms need to be added).

## Implementation Hints
- Use `npx cap init` with positional `appName` and `appId` arguments together with the `--web-dir` flag to avoid the interactive prompt.
- Vite's default build output directory is `dist`; ensure it matches `webDir` in `capacitor.config.ts` (or `.json`).
- The Camera plugin's web fallback dispatches a file picker. Tests will provide a JPEG file to this picker, so do NOT call `Camera.requestPermissions()` or rely on `getUserMedia` directly — `Camera.takePhoto` is sufficient.
- On Web, `result.thumbnail` for `MediaType.Photo` contains the full image base64-encoded; pass it as-is to `Filesystem.writeFile({ data: ... })` (no `encoding` option, so the data is treated as base64 bytes).
- The Filesystem plugin's web implementation creates intermediate directories automatically when `recursive: true` is supplied to `writeFile`. Without that flag, writing to `photos/<file>.jpeg` will fail on the very first capture.
- The Preferences plugin stores raw strings: serialize the index with `JSON.stringify` on write and `JSON.parse` on read. Treat a missing key (`value === null`) as an empty array.
- Expose the gallery module on `window` from your entry point (for example in `src/main.ts`) so the verifier can drive it via `window.gallery.capturePhoto()`, `window.gallery.listPhotos()`, and `window.gallery.deletePhoto(path)`.
- Make sure the module is loaded as an ES module so that the dynamic imports of the Capacitor plugins succeed.

## Acceptance Criteria
- Project path: /home/user/myapp
- Start command: `npm run preview -- --host 0.0.0.0 --port 4173`
- Port: 4173
- `npm run build` must complete without errors and produce a `dist/` directory containing `index.html`.
- `capacitor.config.ts` (or `capacitor.config.json`) must exist at the project root with `appName` equal to `Photo Gallery`, `appId` equal to `com.example.photogallery`, and `webDir` equal to `dist`.
- `package.json` must list `@capacitor/core`, `@capacitor/cli`, `@capacitor/camera`, `@capacitor/filesystem`, and `@capacitor/preferences` as dependencies (any of `dependencies` or `devDependencies`). The installed version of `@capacitor/camera` must be 8.1.0 or newer.
- `npx cap sync` executed after the production build must exit with status 0.
- The served page at `http://localhost:4173/` must contain elements with the HTML ids `capture-btn` and `capture-status`. On initial load (before any capture has been attempted), `#capture-status` must contain the literal text `idle`.
- `window.gallery.capturePhoto`, `window.gallery.listPhotos`, and `window.gallery.deletePhoto` must all be defined as async functions on the served page.
- Calling (or clicking through to) `window.gallery.capturePhoto()` after the file picker provides a JPEG must:
    - Resolve with a string of the form `photos/<isoTimestamp>.jpeg`, where `<isoTimestamp>` is the value of an ISO-8601 timestamp produced by `new Date().toISOString()` (e.g. `photos/2026-01-02T03:04:05.678Z.jpeg`).
    - Cause `Filesystem.readFile({ path: <returned_path>, directory: Directory.Data })` to succeed and return base64 data whose decoded bytes equal the bytes that were fed to the file picker.
    - Append the returned path to the JSON array stored in `@capacitor/preferences` under the key `photo_index`.
    - Transition `#capture-status` to `saved` (when triggered via the button).
- `window.gallery.listPhotos()` must return an array of strings equal to the current JSON-decoded `photo_index` value (or `[]` if the key is unset), and the order MUST reflect insertion order.
- After a full page reload, `window.gallery.listPhotos()` must still return the previously captured paths (i.e. state persists across reloads through Capacitor Preferences and Filesystem).
- `window.gallery.deletePhoto(path)` must:
    - Cause `Filesystem.readFile({ path, directory: Directory.Data })` to subsequently fail.
    - Remove `path` from the `photo_index` array stored in Preferences (the remaining entries must keep their relative order).

