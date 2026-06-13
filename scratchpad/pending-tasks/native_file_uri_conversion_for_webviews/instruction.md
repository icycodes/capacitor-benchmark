Capacitor apps handling local media often return raw native file URIs (e.g., `file:///var/mobile/...`). These URIs fail to load directly in web `<img src="...">` or `<video>` tags due to native WebView security sandboxing and custom schemes.

You need to implement a utility function in `src/utils/imageHandler.ts` that uses the Capacitor core runtime API to safely translate a provided native file URI into a WebView-friendly URL before returning it to the frontend.

**Constraints:**
- Must import and utilize the `Capacitor` object from `@capacitor/core`.
- Do NOT modify any HTML or React/Vue DOM elements; strictly implement the string transformation logic.