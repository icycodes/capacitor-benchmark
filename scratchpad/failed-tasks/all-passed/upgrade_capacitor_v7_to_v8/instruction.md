# Upgrade Capacitor v7 Project to Capacitor v8

## Background
You are handed a Vite + TypeScript project at `/home/user/myapp` that was originally built against Capacitor 7. The project currently has the following `@capacitor/*` dependencies pinned to the v7 line and installed in `node_modules`:

- `@capacitor/core` (runtime dependency)
- `@capacitor/preferences` (runtime dependency)
- `@capacitor/cli` (dev dependency)

The Capacitor configuration file (`capacitor.config.ts`) is already in place with a valid `appId`, `appName`, and `webDir`. A small piece of application code in `src/main.ts` already calls into `@capacitor/preferences`; it must keep compiling and the project must keep building.

Capacitor 8 introduces a few breaking changes you need to be aware of. Most notably, **Capacitor 8 requires Node.js 22 or greater**, and every official Capacitor plugin must be bumped to its 8.x major in lock-step with `@capacitor/core` and `@capacitor/cli` (mixing a v7 plugin with v8 core will cause the CLI to emit a version mismatch warning during `npx cap sync`). The Capacitor CLI is itself a dev dependency that ships an `npx cap migrate` helper, but you may also perform the upgrade manually.

Your job is to upgrade ALL `@capacitor/*` dependencies in the project to the latest Capacitor 8.x release, reinstall, and prove that the project still builds and that `npx cap sync` runs cleanly. You do NOT need to add the native Android or iOS platforms (`@capacitor/android` / `@capacitor/ios`); only the existing packages must be upgraded.

The project starts with the Node.js 22+ runtime already available in the environment, so you do not need to install or change the Node.js version.

## Requirements
- Upgrade EVERY `@capacitor/*` package declared in `/home/user/myapp/package.json` (under `dependencies` and/or `devDependencies`) to the latest Capacitor 8.x release.
- After updating the version specifiers, re-run `npm install` so that the lockfile and the installed package metadata under `node_modules/@capacitor/*` all reflect the v8 release. A `package-lock.json` MUST exist after install.
- `npm run build` must continue to exit `0` and produce `dist/index.html`.
- `npx cap sync` must exit `0`. Its stderr must NOT contain a Capacitor plugin "version mismatch" warning. (The CLI emits one when a `@capacitor/*` plugin's major version does not match the CLI's major version.)
- Do not change the project's `appId`, `appName`, or `webDir` in `capacitor.config.ts`. They must remain exactly as scaffolded.
- Do not add `@capacitor/android` or `@capacitor/ios`. They are out of scope for this upgrade task.

## Implementation Hints
- Capacitor's official upgrade guide for v8 lists the breaking changes you should be aware of: Node 22+ is now the minimum, every official Capacitor plugin (including `@capacitor/preferences`) ships a matching `8.0.0` (or higher) major release, and the recommended automated path is `npm i -D @capacitor/cli@latest` followed by `npx cap migrate`.
- You can also perform the upgrade manually: bump the version specifiers in `package.json` to the v8 majors, then run `npm install` to refresh `node_modules` and regenerate `package-lock.json`.
- The `npx cap sync` command reads `node_modules/@capacitor/*/package.json` for each installed plugin and compares its major version to the CLI's major version. Upgrading every plugin in lock-step is what eliminates the mismatch warning.

## Acceptance Criteria
- Project path: /home/user/myapp
- Every key in `/home/user/myapp/package.json` `dependencies` and `devDependencies` whose name starts with `@capacitor/` has a version specifier whose first dotted segment (after stripping leading semver range operators such as `^`, `~`, `>=`) equals `8`.
- For every `@capacitor/*` package directory present under `/home/user/myapp/node_modules/`, its `package.json` exists and has a `version` field whose first dotted segment equals `8`. This MUST include at minimum `@capacitor/core`, `@capacitor/cli`, and `@capacitor/preferences`.
- A `/home/user/myapp/package-lock.json` file exists and is valid JSON with a `lockfileVersion` field present.
- Running `npm run build` inside `/home/user/myapp` exits with code `0`, and afterwards `/home/user/myapp/dist/index.html` exists.
- Running `npx --no-install cap sync` inside `/home/user/myapp` exits with code `0`, and its stderr does NOT contain the case-insensitive phrase `version mismatch`.
- The `appId`, `appName`, and `webDir` recorded in `/home/user/myapp/capacitor.config.ts` are unchanged from the initial scaffold. A snapshot of the original values is written by the environment to `/home/user/.harbor/initial_capacitor_config.json`; the verifier compares against that file.

