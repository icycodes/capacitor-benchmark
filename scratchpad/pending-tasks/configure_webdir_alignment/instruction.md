# Align Vite Output with Capacitor `webDir`

## Background
You are integrating [Capacitor](https://capacitorjs.com/) (v8) into an existing Vite-based web application. A frequent friction point is a mismatch between the web framework's output directory and the `webDir` declared in `capacitor.config.ts`, which causes errors like `Could not find the web assets directory` when running `npx cap sync`.

Your goal is to initialize Capacitor non-interactively in this project, point Vite's build output at a custom directory, and make sure `webDir` in the Capacitor config matches the same directory so the web build is discoverable.

The project is located at `/home/user/myproject`. It already contains a minimal Vite project with `package.json`, `index.html`, and `src/main.js`. `@capacitor/core` and `@capacitor/cli` are already installed in the project's `node_modules`, and Node.js 22 is available. **Capacitor has NOT yet been initialized — there is no `capacitor.config.ts` / `capacitor.config.json` file yet.**

## Requirements
- Initialize Capacitor for this project, non-interactively (no prompts).
- The app must be initialized with:
  - App name: `Harbor Capacitor Test`
  - App ID: `com.harbor.capacitor.test`
- Vite must build its production output into a directory named `www` at the project root (not the default `dist`).
- `capacitor.config.ts` must declare `webDir` as `www` so it matches Vite's output.
- Running `npm run build` must succeed and produce `www/index.html`.

## Implementation Hints
- The Capacitor CLI's `init` command supports passing the app name, app ID, and web directory as positional/flag arguments to skip the interactive prompts.
- Vite's production output directory is controlled by `build.outDir` in `vite.config.js` / `vite.config.ts`.
- Do not add the native Android or iOS platforms; this task is only about the web-side configuration and build alignment.
- You only need to modify or create configuration files; do not edit the application source code.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Command: `npm run build`
- After running the command from `/home/user/myproject`, the following must be true:
  - The file `/home/user/myproject/www/index.html` exists (Vite has produced its build into the `www` directory).
  - The file `/home/user/myproject/capacitor.config.ts` exists (or `capacitor.config.json` if that format was generated) and declares:
    - `appId`: `com.harbor.capacitor.test`
    - `appName`: `Harbor Capacitor Test`
    - `webDir`: `www`
  - Running `npx cap config --json` from the project root prints a JSON object whose `webDir` field is `www`, `appId` is `com.harbor.capacitor.test`, and `appName` is `Harbor Capacitor Test`.
  - The default `dist/` directory must NOT contain a freshly built `index.html` after `npm run build` (i.e. Vite's output goes to `www`, not `dist`).

