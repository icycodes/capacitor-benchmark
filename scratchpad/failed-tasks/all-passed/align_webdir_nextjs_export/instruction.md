# Align Capacitor `webDir` with Next.js Static Export

## Background
A pre-scaffolded Next.js 14 + TypeScript application uses Capacitor v8 to package the web build as a native shell. The project at `/home/user/myapp` already includes Capacitor core, CLI, and the Android platform, but the configuration is misaligned: `capacitor.config.ts` declares `webDir: "out"`, while `next.config.js` is missing the static export switch. As a result, `npm run build` only emits `.next/` and `npx cap sync` fails with `Could not find the web assets directory: ./out`.

Your job is to repair the configuration so the existing toolchain produces a valid `out/` directory that Capacitor can sync into the Android project.

## Requirements
- Configure the Next.js application to perform a static export at build time so that `npm run build` writes the rendered site to `/home/user/myapp/out/`.
- Keep `capacitor.config.ts` pointing at the `out/` directory (this is already the desired `webDir`).
- Ensure `npm run build` followed by `npx cap sync` both succeed with exit code 0.

## Implementation Hints
- Next.js 14 exposes a top-level `output` option in `next.config.js`. Setting it to the value documented for static exports causes `next build` to populate the `out/` directory instead of (or in addition to) `.next/`.
- Capacitor's `webDir` field must match the directory that actually contains `index.html` after the build. Do not change `webDir`; align the build output with it.
- After fixing the config, you can validate locally by running `npm run build` and then `npx cap sync android`.

## Acceptance Criteria
- Project path: /home/user/myapp
- `next.config.js` (or `next.config.mjs` / `next.config.ts`) declares Next.js static export by setting the `output` option to `'export'`.
- `capacitor.config.ts` keeps `webDir` set to `"out"`.
- Running `npm run build` inside `/home/user/myapp` exits with code 0 and produces `/home/user/myapp/out/index.html`.
- Running `npx cap sync` inside `/home/user/myapp` exits with code 0 and its stderr does NOT contain the string `Could not find the web assets directory`.

