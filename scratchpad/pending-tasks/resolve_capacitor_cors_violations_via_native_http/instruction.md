Standard web `fetch` requests inside the native WebView often fail with CORS errors (e.g., `Origin capacitor://localhost is not allowed`) because external APIs typically do not whitelist custom native application schemes.

You need to update the `capacitor.config.ts` file to enable the `CapacitorHttp` feature, which automatically intercepts browser-level HTTP requests and routes them through native iOS/Android networking libraries to bypass web-based CORS restrictions.

**Constraints:**
- Modifications must be strictly limited to the `capacitor.config.ts` configuration file.
- Do NOT alter any existing frontend `fetch()` or `axios` application code.