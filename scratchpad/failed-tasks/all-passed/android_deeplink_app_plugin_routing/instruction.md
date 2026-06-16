# Configure Android App Links and Deep-Link Routing for a Capacitor v8 App

## Background
You are working on a Capacitor v8 hybrid mobile application located at `/home/user/myapp`. The project already has the `android` platform scaffolded at `/home/user/myapp/android`, a minimal web frontend in `/home/user/myapp/dist`, and the `@capacitor/app` plugin already installed under `node_modules` (and listed in `package.json`).

The product team wants the app to act as the default handler for `https://myapp.example.com/...` web URLs (Android App Links) so that taps on those URLs from email, browsers, or other apps open the native app directly instead of a browser. When the app is launched (or resumed) via such a URL, the SPA must read the incoming URL and route accordingly.

Your job is to wire everything up: declare a verifiable App-Link intent filter for `MainActivity` in `AndroidManifest.xml`, write the Digital Asset Links file (`assetlinks.json`) that the team will deploy to `https://myapp.example.com/.well-known/assetlinks.json`, and add a TypeScript handler that subscribes to the `appUrlOpen` event from `@capacitor/app` to drive client-side routing.

## Requirements
- Modify `android/app/src/main/AndroidManifest.xml` so that the existing `MainActivity` (`<activity android:name=".MainActivity" ...>`) declares an additional App-Link `<intent-filter>` with the following properties:
  - `android:autoVerify="true"` on the `<intent-filter>` element.
  - Action `android.intent.action.VIEW`.
  - Both categories `android.intent.category.DEFAULT` and `android.intent.category.BROWSABLE`.
  - A `<data>` declaration that pins `android:scheme="https"` and `android:host="myapp.example.com"`.
  - The intent filter must cover URLs under the `/.well-known/` path of that host (e.g. via `android:pathPrefix="/.well-known"` or `android:pathPattern="/.well-known/.*"`).
- The original `MAIN` / `LAUNCHER` intent filter on `MainActivity` must remain in place — this new intent filter is **additional**, not a replacement.
- Create a Digital Asset Links file at `/home/user/myapp/.well-known/assetlinks.json` whose contents are valid JSON of the form documented for Android App Links. Specifically, the file must be a JSON array of statement objects; at least one statement must:
  - Declare the relation `delegate_permission/common.handle_all_urls`.
  - Have a `target` whose `namespace` is `"android_app"`, whose `package_name` is `"com.example.myapp"`, and whose `sha256_cert_fingerprints` array contains the SHA-256 fingerprint of the Android debug signing certificate that ships with this project (the keystore at `$HOME/.android/debug.keystore` that the prebuilt Gradle wrapper uses).
- Create a TypeScript module at `/home/user/myapp/src/deeplink.ts` that:
  - Imports `App` from the `@capacitor/app` package (named import, e.g. `import { App } from '@capacitor/app'`).
  - Exports a function (any name) that registers a listener via `App.addListener('appUrlOpen', ...)` and, inside that listener, derives a route path from the incoming URL (i.e. uses `new URL(event.url).pathname` or an equivalent parse) and updates the SPA location (e.g. `window.location.replace(...)`, `window.history.replaceState(...)`, or an equivalent SPA route-change call) using that pathname.
  - Exports the registration function so it can be imported and invoked from the app entry point.
- `package.json` must continue to list `@capacitor/app` as a runtime dependency (it is already present in the starter state — do not remove it).
- The Android project must still build successfully via the prebuilt Gradle wrapper.

## Implementation Hints
- Refer to the Android App Links guide (`https://developer.android.com/training/app-links/verify-android-applinks`) and the Capacitor `@capacitor/app` plugin docs (`https://capacitorjs.com/docs/apis/app`). The latter describes the `appUrlOpen` event payload (`URLOpenListenerEvent`, which carries a `url: string`).
- Add the new `<intent-filter>` *inside* the existing `<activity android:name=".MainActivity" ...>` element in `AndroidManifest.xml`. Do not create a separate activity.
- Remember that `<intent-filter>`'s `android:autoVerify` attribute, together with at least one `https`-scheme `<data>` element, is what makes this an *App Link* rather than just a deep link.
- To compute the SHA-256 fingerprint of the debug keystore, use `keytool` (already on the PATH because the JDK is installed). The default debug keystore password is `android` and the default alias is `androiddebugkey`. The relevant Capacitor build uses the keystore at `$HOME/.android/debug.keystore`, which has already been created during the prebuilt warm-up Gradle build.
- On the JavaScript side, the `@capacitor/app` plugin emits `appUrlOpen` with `{ url: string, ... }`. You can pass that `url` into `new URL(url)` to extract the `pathname` to feed your client-side router.
- The Android SDK, JDK, and Gradle wrapper are pre-installed and pre-warmed. From `/home/user/myapp/android` you can compile with `./gradlew :app:assembleDebug --offline`.
- You do not need to install any npm packages — `@capacitor/app` is already installed.

## Acceptance Criteria
- Project path: `/home/user/myapp`
- The Android project at `/home/user/myapp/android` must build successfully via:
  - `cd /home/user/myapp/android && ./gradlew :app:assembleDebug --offline`
- `android/app/src/main/AndroidManifest.xml` must contain, *inside* the `<activity android:name=".MainActivity" ...>` element, an `<intent-filter>` that:
  - Has `android:autoVerify="true"`.
  - Declares `<action android:name="android.intent.action.VIEW" />`.
  - Declares both `<category android:name="android.intent.category.DEFAULT" />` and `<category android:name="android.intent.category.BROWSABLE" />`.
  - Declares a `<data ...>` entry that pins scheme `https` and host `myapp.example.com`, and that restricts the path to `/.well-known/` (via `android:pathPrefix="/.well-known"` or `android:pathPattern="/.well-known/.*"`).
  - The original `MAIN` / `LAUNCHER` intent filter on `MainActivity` must still be present.
- A file at `/home/user/myapp/.well-known/assetlinks.json` must exist and parse as a JSON array of one or more statement objects. At least one statement must declare:
  - A `relation` array containing `"delegate_permission/common.handle_all_urls"`.
  - A `target` object with `namespace == "android_app"`, `package_name == "com.example.myapp"`, and a `sha256_cert_fingerprints` array of non-empty strings, one of which equals the SHA-256 fingerprint of the certificate stored under alias `androiddebugkey` in `$HOME/.android/debug.keystore` (password `android`).
- A TypeScript module must exist at `/home/user/myapp/src/deeplink.ts` and must:
  - Import `App` from `@capacitor/app` (named import).
  - Register a listener via `App.addListener('appUrlOpen', ...)` (single-quoted or double-quoted event name accepted).
  - Inside the listener body, use `new URL(...)` to parse the incoming URL and call a route-changing browser API (one of `window.location.replace(...)`, `window.location.assign(...)`, `window.location.href = ...`, or `window.history.replaceState/pushState(...)`) with the parsed `pathname`.
  - Export the registration function (named export OR default export — both are acceptable).
- `package.json` `dependencies` must still contain `@capacitor/app`.

