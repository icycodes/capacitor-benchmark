# Capacitor v8 HTTP Bearer Token Wrapper

## Background
You are extending a freshly initialized Capacitor v8 app located at `/home/user/myproject`. The frontend talks to a third-party REST API whose backend does not send permissive CORS headers, so the team has decided to route every outbound request through `CapacitorHttp` (the native HTTP client bundled with `@capacitor/core`).

The team also wants a single, reusable TypeScript helper that:

- Injects an `Authorization: Bearer <token>` header on every request, pulling the token from the `@capacitor/preferences` store under the key `auth_token`.
- Serializes JSON request bodies for POST/PUT-style helpers.
- Detects expired/invalid tokens (HTTP 401) by clearing the stored token and re-throwing a typed error so the UI can react to it.
- Returns strongly-typed responses so consumers don't have to manually cast `response.data`.

The project already has Capacitor and its plugins installed; you only need to wire up the configuration, write the helper module, and make sure it compiles cleanly.

## Requirements

1. Enable native HTTP routing by adding the `CapacitorHttp` plugin block (with `enabled: true`) to the `plugins` object exported from `capacitor.config.ts`. Existing config fields (`appId`, `appName`, `webDir`) must be preserved.
2. Create a new TypeScript module at `src/api/httpClient.ts` that exports the API below. The module **must** use `CapacitorHttp.request` from `@capacitor/core` (do **not** call `CapacitorHttp.get`/`post` directly) and **must** use `Preferences` from `@capacitor/preferences` to read/clear the token.
3. The TypeScript project must compile without errors via `npm run build` (which runs `tsc --noEmit`). The exported symbols must be type-safe (use the generic type parameter when possible) and must not rely on `any` for the return values.

### Exported API

The module must export the following symbols with these exact names:

```ts
export interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Record<string, string>;
}

export class UnauthorizedError extends Error {
  status: 401;
  url: string;
}

export function httpGet<T = unknown>(
  url: string,
  params?: Record<string, string>,
): Promise<ApiResponse<T>>;

export function httpPost<T = unknown, B = unknown>(
  url: string,
  body?: B,
): Promise<ApiResponse<T>>;
```

### Behavior Contract

The helpers must implement the following behavior when invoked:

- **Token injection**: Before every request, read the value stored under the `auth_token` key from `Preferences`. If a non-null token is found, attach the header `Authorization: Bearer <token>`. If the token is `null`, send the request without the `Authorization` header.
- **GET**: Calls `CapacitorHttp.request` with `method: 'GET'`, the supplied `url`, and (when provided) the `params` object passed through verbatim as the `params` request option. The `Content-Type` header must **not** be set on GET requests.
- **POST**: Calls `CapacitorHttp.request` with `method: 'POST'`, the supplied `url`, the body assigned to `data` (the helper is responsible for JSON-serializing the body — assign the original object/value to `data` and add the header `Content-Type: application/json`). If `body` is `undefined`, no `data` field should be set and no `Content-Type` header should be added.
- **401 handling**: If the response status is exactly `401`, the helper must (a) remove the `auth_token` key from `Preferences` and (b) throw an `UnauthorizedError` whose `message` includes the request URL, `status` is `401`, and `url` matches the request URL. The error must not be swallowed.
- **Other non-2xx**: For any status outside the 200–299 range (and not 401), the helper must throw a regular `Error` whose `message` contains the status code (e.g. `HTTP 500`). `Preferences` must **not** be cleared in this case.
- **2xx responses**: Return an `ApiResponse<T>` whose `data` is the raw response body returned by `CapacitorHttp.request`, `status` is the numeric status, and `headers` is the headers object.

## Implementation Hints

- The TypeScript types for `CapacitorHttp.request` live in `@capacitor/core` (`HttpOptions`, `HttpResponse`). Import them by name rather than redeclaring them.
- `Preferences.get({ key })` resolves to `{ value: string | null }`. Treat `null` and the empty string as "no token".
- Centralize the request logic in a single private function so that `httpGet` and `httpPost` share the token-injection and 401-handling code path.
- Construct the headers object as a fresh `Record<string, string>` per request so that callers cannot accidentally mutate a shared object.

## Acceptance Criteria

- Project path: `/home/user/myproject`
- Command: `npm run build` (this runs `tsc --noEmit` against the project)
  - The command must exit with code `0`.
- `capacitor.config.ts` must export a `CapacitorConfig` whose `plugins.CapacitorHttp.enabled` is `true`. The existing `appId`, `appName`, and `webDir` fields must remain intact.
- `src/api/httpClient.ts` must exist and export `httpGet`, `httpPost`, `UnauthorizedError`, and the `ApiResponse` interface with the signatures described above.
- The module's runtime behavior must satisfy the Behavior Contract section. Behavior is verified by running a Node.js test harness that mocks `@capacitor/core` and `@capacitor/preferences` and exercises the exported functions.

