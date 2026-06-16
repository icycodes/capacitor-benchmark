# Install @capacitor/dialog v8 and Wire a Prompt Button That Renders the Result

## Background
[`@capacitor/dialog`](https://capacitorjs.com/docs/apis/dialog) is the official Capacitor v8 plugin used to show native alert, confirm, and prompt dialogs. On the web, the plugin falls back to the browser's native `window.alert`, `window.confirm`, and `window.prompt`. The `Dialog.prompt({ title, message })` call resolves with a `PromptResult` of shape `{ value: string, cancelled: boolean }`, where `cancelled` is `true` exactly when the underlying `window.prompt` returns `null`.

A Vite + TypeScript project pre-scaffolded with Capacitor v8 already exists at `/home/user/myapp`. The project builds and syncs cleanly, but it does NOT yet depend on `@capacitor/dialog` and does NOT yet wire any prompt UI. Your task is to install the plugin from npm at the v8 major version, then add a small UI to the page that calls `Dialog.prompt(...)` when a button is clicked and writes the result into a sibling `<span>`.

## Requirements
- Add `@capacitor/dialog` to the project's `dependencies` at the v8 major version (`^8.x.x` or any specifier that resolves to a v8 release).
- The page served from `dist/index.html` (the same `index.html` that Vite uses as the entry) must render two elements with stable identifiers:
    - A button with `id="prompt-btn"`.
    - A span (or other text container) with `id="prompt-result"`.
- Clicking `#prompt-btn` must invoke `Dialog.prompt({ title: 'Your name', message: 'Enter name' })`.
- When the returned promise resolves:
    - If `cancelled === false`, the resolved `value` string must be placed into `#prompt-result.textContent`.
    - If `cancelled === true`, the literal string `cancelled` must be placed into `#prompt-result.textContent`.
- After your changes, `npm run build` and `npx cap sync` must both still exit with code 0, and the production build at `dist/index.html` must exist.

## Implementation Hints
- Install the plugin with `npm install @capacitor/dialog@^8`, then re-run `npx cap sync` so the native projects pick up the new package.
- Import the plugin from its ESM entry: `import { Dialog } from '@capacitor/dialog';`. Capacitor v8 ships TypeScript types out of the box, so no extra `@types/...` package is needed.
- The plugin's web fallback resolves the prompt promise with `{ value: '', cancelled: true }` when the underlying `window.prompt` returns `null`. Branch on `cancelled` (not on `value`) to decide what to render.
- You can wire the button in the existing `src/main.ts` entry module (already loaded by `index.html`), or in any other module imported from it. Make sure the click handler is attached after the DOM nodes exist.
- `Dialog.prompt(...)` returns a Promise, so use `async/await` or `.then(...)` to read `value` and `cancelled`.

## Acceptance Criteria
- Project path: /home/user/myapp
- Start command: `npm run preview -- --host 0.0.0.0 --port 4173`
- Port: 4173
- `/home/user/myapp/package.json` declares `@capacitor/dialog` in `dependencies` with a resolved semver major equal to `8`.
- `npm run build` exits with status 0 and produces `/home/user/myapp/dist/index.html`.
- `npx cap sync` exits with status 0.
- The page served by the Vite preview at `http://localhost:4173/` exposes both `#prompt-btn` and `#prompt-result` in the DOM.
- Browser behavior verified through a headless Chromium (Playwright) preview-server run on two fresh contexts:
    - Context A: with `window.prompt` overridden via `add_init_script` to return the string `Pochi`, clicking `#prompt-btn` must update `#prompt-result.textContent` to exactly `Pochi` within 10 seconds.
    - Context B: with `window.prompt` overridden via `add_init_script` to return `null`, clicking `#prompt-btn` must update `#prompt-result.textContent` to exactly the literal string `cancelled` within 10 seconds.

