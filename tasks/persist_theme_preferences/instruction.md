# Persist User Theme with Capacitor Preferences

## Background
You are building a small Vite + TypeScript web application that will be packaged as a native mobile app via Capacitor v8. To survive native OS storage sweeps, persistent user settings must be stored using the `@capacitor/preferences` plugin instead of the unreliable `window.localStorage`. The Preferences plugin falls back to `localStorage` when the app is served as a Progressive Web App in the browser, so the same code works in the web build that this task will exercise.

A minimal Vite TypeScript project has already been scaffolded for you at `/home/user/myapp`. Your job is to integrate Capacitor v8, install the Preferences plugin, and implement a dark/light theme toggle whose value persists across reloads via Capacitor's Preferences API.

## Requirements
- Integrate Capacitor v8 into the existing Vite project using the non-interactive CLI flow. The Capacitor app must be configured with:
    - App name: `Theme Demo`
    - Application/package id: `com.example.themedemo`
    - Web assets directory aligned with Vite's build output (`dist`).
- Install and use the `@capacitor/preferences` plugin (version compatible with Capacitor v8) for persistence.
- Implement a UI in `index.html` that includes a button users can click to toggle between `light` and `dark` themes.
- Persist the currently selected theme under the Preferences key `user_theme` (value `"light"` or `"dark"`).
- On every page load, read the saved theme from Capacitor Preferences and apply it before the user interacts. If no value has been stored yet, default to `light`.
- Toggling the button must update the visible theme, save the new value through `Preferences.set`, and keep working across full page reloads.
- Reflect the active theme on the `<body>` element by toggling a single CSS class named `dark` (present when dark mode is on, absent when light mode is on).
- `npx cap sync` must run successfully against the produced web build.

## Implementation Hints
- Use `npx cap init` with positional `appName` and `appId` arguments and the `--web-dir` flag to avoid the interactive prompt.
- Import `Preferences` from `@capacitor/preferences` in your TypeScript code; the API is `await Preferences.set({ key, value })` and `const { value } = await Preferences.get({ key })`.
- Vite's default build output directory is `dist`, which must match `webDir` in `capacitor.config.ts` (or `.json`).
- The Preferences plugin transparently falls back to `localStorage` on the web target, so no native runtime is required for the web build used to verify the behavior.
- Make sure the script that wires up the toggle is loaded as an ES module so that the dynamic import of `@capacitor/preferences` succeeds.

## Acceptance Criteria
- Project path: /home/user/myapp
- Start command: `npm run preview -- --host 0.0.0.0 --port 4173`
- Port: 4173
- `npm run build` must complete without errors and produce a `dist/` directory containing `index.html`.
- `capacitor.config.ts` (or `capacitor.config.json`) must exist at the project root with `appName` equal to `Theme Demo`, `appId` equal to `com.example.themedemo`, and `webDir` equal to `dist`.
- `package.json` must list `@capacitor/core`, `@capacitor/cli`, and `@capacitor/preferences` as dependencies (any of `dependencies` or `devDependencies`).
- `npx cap sync --inline` (or `npx cap sync`) executed after the production build must exit with status 0.
- The served page at `http://localhost:4173/` must contain a single visible toggle button with the HTML id `theme-toggle`.
- Loading `http://localhost:4173/` in a fresh browser session must apply the `light` theme by default; the `<body>` element must NOT have the CSS class `dark`.
- Clicking the `#theme-toggle` button once must add the CSS class `dark` to the `<body>` element.
- After clicking the button to enable dark mode and reloading the page, the `<body>` element must still have the CSS class `dark` (the value must persist through Capacitor Preferences).
- Clicking the button again must remove the `dark` class from `<body>`, and that lighter state must also persist across a reload.

