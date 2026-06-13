To accelerate UI development, developers proxy the Capacitor WebView to a local Vite dev server (e.g., `http://192.168.1.100:5173`). However, modern mobile operating systems block this unencrypted HTTP traffic by default, resulting in a `net::ERR_CLEARTEXT_NOT_PERMITTED` error on Android.

You need to modify the `server` block in `capacitor.config.ts` to point the app to the local development URL and explicitly allow unencrypted cleartext traffic so the required manifest permissions are automatically injected.

**Constraints:**
- Must set the live reload URL strictly to `http://192.168.1.100:5173`.
- Must properly configure the cleartext flag within the configuration object to satisfy Android's security policies.