# Bypass CORS in a Capacitor App with CapacitorHttp

## Background
A pre-existing Capacitor v8 project at `/home/user/myproject` is failing CORS preflight checks when calling third-party APIs from the WebView, because the requests originate from `capacitor://localhost` / `http://localhost`. Capacitor ships with a built-in **CapacitorHttp** plugin that, when enabled, patches `window.fetch` / `XMLHttpRequest` to use the native HTTP stack and side-steps WebView CORS entirely. The same plugin also exposes helper methods (`CapacitorHttp.get`, `CapacitorHttp.post`, etc.) directly from `@capacitor/core`.

Your job is to (1) enable CapacitorHttp in the Capacitor configuration and (2) provide a small Node-runnable CLI wrapper that uses the CapacitorHttp helper API so the team can smoke-test outbound requests from CI without having to spin up a device or simulator.

## Requirements
- Enable the `CapacitorHttp` plugin in `capacitor.config.ts`.
- Implement a TypeScript-based CLI in the project that uses the `CapacitorHttp` API exported from `@capacitor/core` to make GET and POST requests against a remote URL.
- The CLI must accept the HTTP method, URL, optional JSON body, and an optional custom header so it can be parametrized from the test runner.
- Print the response **status code** on the first line of stdout and the response **body** (serialized as JSON) on the second line of stdout.
- Reuse the project's existing TypeScript / Node toolchain — no additional HTTP libraries (e.g., `axios`, `node-fetch`) are allowed; the actual request must go through `CapacitorHttp`.

## Implementation Hints
- The CapacitorHttp configuration lives under `plugins.CapacitorHttp` in `capacitor.config.ts`. Setting `enabled: true` activates the fetch/XHR patch on native.
- `CapacitorHttp` is re-exported from `@capacitor/core` and exposes promise-based helpers such as `get`, `post`, and `request`, each accepting an `HttpOptions` object (`url`, `headers`, `data`, ...).
- When run inside Node (i.e., the verifier sandbox), CapacitorHttp falls back to the web implementation, which calls `fetch` under the hood — this is the behavior you can rely on for the CLI.
- Use Node 22's built-in argument parsing (`process.argv`) or any helper already present in `node_modules`; you do not need to install new packages.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Command: `npx tsx scripts/http-cli.ts --method <GET|POST> --url <url> [--body <json-string>] [--header <Name:Value>]`
  - `--method`: HTTP verb, either `GET` or `POST`.
  - `--url`: Absolute URL of the remote endpoint.
  - `--body`: Optional JSON string to send as the request body (only meaningful for `POST`).
  - `--header`: Optional extra HTTP header in `Name:Value` form. May be omitted.
- Stdout format (exactly two lines, no extra wrapping text):
  - Line 1: `Status: <numeric_status_code>`
  - Line 2: A single JSON object containing the parsed response body returned by `CapacitorHttp`.
- `capacitor.config.ts` must export a config where `plugins.CapacitorHttp.enabled` is `true`.
- The CLI script must import `CapacitorHttp` from `@capacitor/core` (no direct use of `fetch`, `axios`, `node-fetch`, `http`, or `https` modules).
- Use the `ZEALT_RUN_ID` environment variable when the verifier needs to disambiguate requests — the verifier will pass `run-id` values via `--header` and query parameters, and the CLI must forward them faithfully to the remote endpoint.

