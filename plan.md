# Capacitor (v8) Benchmark Research Plan

This research plan is designed to guide the creation of realistic evaluation datasets and benchmark tasks for AI coding agents working with **Capacitor v8**. It skips interactive/device-debugging features (like live-reload or native IDE debugging) in favor of headless compilation, configuration, and API-integration tasks suitable for a non-interactive Docker container.

---

## 1. Library Overview

### Description
[Capacitor](https://capacitorjs.com/) is a cross-platform native runtime developed by Ionic that enables developers to build modern, performant web-native mobile applications. It allows standard web apps (HTML, CSS, JavaScript) to run inside a native container on iOS, Android, and Web/PWA, providing unified JavaScript APIs to access native device SDKs.

### Ecosystem Role
Capacitor acts as a modern replacement for Apache Cordova. It sits between a web frontend framework (e.g., React, Vue, Angular, Svelte, SolidJS) and the native mobile platform (iOS, Android). Unlike Cordova, which treats native platforms as build-time artifacts, Capacitor treats native projects (`/ios` and `/android` directories) as **source assets** that are committed to source control and configured directly using native IDEs (Android Studio, Xcode).

### Project Setup (Non-Interactive CLI)
To bootstrap or integrate Capacitor v8 into a project within a non-interactive environment (like a Docker container), developers use the following automated flow:

1. **Install Core Dependencies**:
   Ensure Node.js 22+ is installed, then add Capacitor core and CLI to an existing web project:
   ```bash
   npm install @capacitor/core
   npm install -D @capacitor/cli@latest
   ```

2. **Initialize Capacitor Config (Non-Interactive)**:
   Avoid the interactive prompt by passing the app name, package ID, and build directory directly:
   ```bash
   npx cap init "My Native App" "com.example.myapp" --web-dir dist
   ```

3. **Install Mobile Platforms**:
   Add the native Android and iOS platform packages:
   ```bash
   npm install @capacitor/android@latest @capacitor/ios@latest
   ```

4. **Add Platforms to Project**:
   Scaffold the native project directories (`/android` and `/ios`):
   ```bash
   npx cap add android
   npx cap add ios
   ```

5. **Sync Web Assets and Plugins**:
   Copy the compiled web assets (from `dist`) and update native dependencies/plugins:
   ```bash
   # Ensure frontend is built first
   npm run build
   # Sync assets and plugins to native platforms
   npx cap sync
   ```

---

## 2. Core Primitives & APIs

Capacitor utilizes a set of official, modular plugins to access native capabilities. Below are the key APIs in v8, including specific documentation links and implementation examples.

### Core API Reference Links
* [Device API Docs](https://capacitorjs.com/docs/apis/device): Access hardware/OS details (model, battery, language).
* [Preferences API Docs](https://capacitorjs.com/docs/apis/preferences): Lightweight, persistent key-value storage (replaces unstable `localStorage`).
* [Filesystem API Docs](https://capacitorjs.com/docs/apis/filesystem): Read, write, and manage files on the native device storage.
* [Camera API Docs](https://capacitorjs.com/docs/apis/camera): Capture photos/videos or pick from the gallery.
* [Geolocation API Docs](https://capacitorjs.com/docs/apis/geolocation): Query GPS and track location changes.
* [Capacitor Cookies & Http Docs](https://capacitorjs.com/docs/apis/http): Native network utilities bypassing browser CORS restrictions.
* [Custom Native Code (Android)](https://capacitorjs.com/docs/android/custom-code) / [(iOS)](https://capacitorjs.com/docs/ios/custom-code): Custom local plugins.

---

### Detailed API Implementations & Snippets (v8)

#### A. Camera API (New v8.1.0+ Media API)
Capacitor v8.1.0 introduces a modernized, robust Camera API that deprecates `getPhoto` and `pickImages`. It replaces `resultType` with a unified `MediaResult` object containing fixed properties for both photos and videos.

**TypeScript Usage:**
```typescript
import { Camera, MediaType } from '@capacitor/camera';

async function captureMedia() {
  try {
    // Take a photo with the camera (replaces getPhoto)
    const photoResult = await Camera.takePhoto({
      quality: 90,
      targetWidth: 1280,
      targetHeight: 720,
      saveToGallery: true,
      includeMetadata: true
    });

    console.log('Photo URI:', photoResult.uri); // Native file URI
    console.log('Photo Web Path:', photoResult.webPath); // Set directly as <img src>
    console.log('Is Photo:', photoResult.type === MediaType.Photo);

    // Record a video (new in v8.1.0)
    const videoResult = await Camera.recordVideo({
      saveToGallery: false,
      includeMetadata: true
    });
    console.log('Video duration:', videoResult.metadata?.duration);
  } catch (error) {
    console.error('Camera action failed', error);
  }
}
```

---

#### B. Preferences API (State Persistence)
The Preferences API provides reliable, lightweight key-value storage across app reloads and OS garbage collection sweeps.

**TypeScript Usage:**
```typescript
import { Preferences } from '@capacitor/preferences';

// Persist a setting
async function saveThemePreference(theme: 'dark' | 'light') {
  await Preferences.set({
    key: 'user_theme',
    value: theme,
  });
}

// Retrieve a setting
async function getThemePreference(): Promise<string | null> {
  const { value } = await Preferences.get({ key: 'user_theme' });
  return value;
}
```

---

#### C. Custom Local Native Plugins (JS-Native Bridge)
When official plugins are insufficient, developers build local plugins directly inside their application's native projects.

##### 1. Android Implementation (Java)
Create `EchoPlugin.java` in `android/app/src/main/java/com/example/myapp/plugins/`:
```java
package com.example.myapp;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "Echo")
public class EchoPlugin extends Plugin {
    @PluginMethod
    public void echo(PluginCall call) {
        String value = call.getString("value");
        JSObject ret = new JSObject();
        ret.put("value", value);
        call.resolve(ret);
    }
}
```
Register the plugin in `MainActivity.java`:
```java
package com.example.myapp;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(EchoPlugin.class); // Register custom local plugin
        super.onCreate(savedInstanceState);
    }
}
```

##### 2. iOS Implementation (Swift)
Create `EchoPlugin.swift` in Xcode under the `App` group:
```swift
import Capacitor

@objc(EchoPlugin)
public class EchoPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "EchoPlugin"
    public let jsName = "Echo"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "echo", returnType: CAPPluginReturnPromise)
    ]

    @objc func echo(_ call: CAPPluginCall) {
        let value = call.getString("value") ?? ""
        call.resolve(["value": value])
    }
}
```
Register the plugin in `MyViewController.swift` (or the app delegate):
```swift
override open func capacitorDidLoad() {
    bridge?.registerPluginInstance(EchoPlugin())
}
```

##### 3. JavaScript Interface
Link the native implementations in your web application:
```typescript
import { registerPlugin } from '@capacitor/core';

interface EchoPluginInterface {
  echo(options: { value: string }): Promise<{ value: string }>;
}

const Echo = registerPlugin<EchoPluginInterface>('Echo');

async function testBridge() {
  const result = await Echo.echo({ value: 'Hello Native!' });
  console.log(result.value); // Prints: 'Hello Native!'
}
```

---

## 3. Real-World Use Cases & Templates

### Templates and Showcase Projects
* [SolidJS + Vite Template](https://github.com/ionic-team/capacitor-solidjs-templates): Official production-ready template for SolidJS and Vite compiled for Capacitor.
* [Remix.run Templates](https://github.com/ionic-team/capacitor-remix-templates): Repository containing native-ready setups for Remix across various runtimes (Express, Vercel, Cloudflare).
* [Next.js + Tailwind Starter](https://github.com/mlynch/nextjs-tailwind-ionic-capacitor-starter): A popular starting point by Max Lynch (co-creator of Capacitor) demonstrating static exports with Next.js, Tailwind CSS, and Ionic Framework.

### Common Integration Patterns
* **Static Site Generation (SSG)**: Since Capacitor serves files locally from device storage, frameworks like Next.js or Remix must be configured for static export (e.g., `output: 'export'` in Next.js). Server-side rendering (SSR) is not supported for offline native execution.
* **Hybrid Routing**: Routing must rely on client-side hash or memory-based history routers (e.g., React Router, Vue Router in hash mode) to prevent native webview navigation errors when reloading local assets.

---

## 4. Developer Friction Points

These friction points make excellent evaluation tasks to test an agent's troubleshooting and configuration abilities.

### Friction Point 1: CORS Origin Issues on External API Requests
* **Description**: Native web requests fail when communicating with standard backends because Capacitor runs under non-standard origins.
* **Symptom**: Console error: `Origin capacitor://localhost is not allowed by Access-Control-Allow-Origin.`
* **Underlying Cause**: Capacitor serves local web content from `capacitor://localhost` (iOS) and `http://localhost` (Android). Remote servers reject these non-standard origins unless CORS headers are customized.
* **Resolution**:
  1. Add `capacitor://localhost` and `http://localhost` to the backend's `Access-Control-Allow-Origin` headers.
  2. Alternatively, enable `CapacitorHttp` in `capacitor.config.ts` to route requests through native HTTP clients, bypassing CORS entirely:
     ```typescript
     const config: CapacitorConfig = {
       plugins: {
         CapacitorHttp: { enabled: true }
       }
     };
     ```
* **Link**: [Ionic CORS Troubleshooting Guide](https://ionicframework.com/docs/troubleshooting/cors)

### Friction Point 2: Web Directory Mismatch on Sync
* **Description**: Syncing fails or copies stale files because of a configuration mismatch between the frontend bundler and Capacitor.
* **Symptom**: CLI error: `[error] Could not find the web assets directory: ./dist. Please create it and make sure it has an index.html file.`
* **Underlying Cause**: The build output directory of the web framework (e.g., Vite outputting to `dist`, Next.js outputting to `out`) does not match the `webDir` value declared in `capacitor.config.ts`.
* **Resolution**: Align the frontend bundler config with the `webDir` parameter in `capacitor.config.ts`. Run the web build command (`npm run build`) before executing `npx cap sync`.
* **Link**: [Capacitor Issue #4029](https://github.com/ionic-team/capacitor/issues/4029)

### Friction Point 3: Android Custom Scheme Origin Truncation
* **Description**: Custom schemes configured on Android behave unexpectedly, breaking backend CORS setups.
* **Symptom**: Backend rejects requests with CORS errors even though `app://localhost` is whitelisted.
* **Underlying Cause**: When setting `androidScheme: 'app'` in `capacitor.config.ts`, Chromium's WebView truncates the origin to `app://` (stripping `localhost`), whereas iOS correctly sends `app://localhost`.
* **Resolution**: Whitelist both `app://` and `app://localhost` on the backend, or use standard `https` with a custom hostname:
  ```typescript
  server: {
    androidScheme: 'https',
    hostname: 'myapp.example.com'
  }
  ```
* **Link**: [Capacitor Issue #6936](https://github.com/ionic-team/capacitor/issues/6936)

---

## 5. Evaluation Ideas

Below is a range of benchmark tasks for testing AI coding agents.

1. **Configure Custom Output Directories** (Difficulty: *Simple*)
   * Task: Align a custom Vite output directory with the `webDir` property in `capacitor.config.ts` and sync the project successfully.
2. **Display Native Device Battery Info** (Difficulty: *Simple*)
   * Task: Integrate the `@capacitor/device` plugin to fetch and render the device's battery level on a web interface.
3. **Persist User Theme State** (Difficulty: *Medium*)
   * Task: Implement a dark/light mode toggle that saves and retrieves the user's preference using `@capacitor/preferences`.
4. **Download and Verify PDF In Filesystem** (Difficulty: *Medium*)
   * Task: Implement a feature to download a PDF from a remote URL and store it locally using `@capacitor/filesystem` under the Documents directory.
5. **Configure Bypassing of CORS Restrictions** (Difficulty: *Complex*)
   * Task: Enable and configure `CapacitorHttp` to allow a web application to successfully execute requests to a CORS-restricted third-party API.
6. **Implement a Custom Local Android Plugin** (Difficulty: *Complex*)
   * Task: Write a custom Java-based Capacitor plugin that returns a mocked hardware sensor reading, register it in `MainActivity`, and expose it to JavaScript.
7. **Implement a Custom Local iOS Plugin** (Difficulty: *Complex*)
   * Task: Write a custom Swift-based Capacitor plugin implementing the `CAPBridgedPlugin` protocol, register it in Xcode's view controller, and expose it to JavaScript.

---

## 6. Sources

1. [Capacitor Official Documentation](https://capacitorjs.com/docs) - Core documentation for the Capacitor native runtime.
2. [Capacitor Environment Setup](https://capacitorjs.com/docs/getting-started/environment-setup) - System requirements and non-interactive environment setup.
3. [Capacitor CLI Command - cap init](https://capacitorjs.com/docs/cli/commands/init) - Reference for non-interactive project initialization parameters.
4. [Capacitor 8.0 Upgrade Guide](https://capacitorjs.com/docs/updating/8-0) - Breaking changes, dependency updates, and Gradle/Kotlin versions for v8.
5. [Capacitor Camera API Docs](https://capacitorjs.com/docs/apis/camera) - Detailed specifications for the new v8.1.0 `takePhoto` and `recordVideo` APIs.
6. [Capacitor Preferences API Docs](https://capacitorjs.com/docs/apis/preferences) - Reference for key-value storage.
7. [Capacitor Filesystem API Docs](https://capacitorjs.com/docs/apis/filesystem) - Reference for local file read/write operations.
8. [Custom Native Android Code](https://capacitorjs.com/docs/android/custom-code) - Guide to creating and registering local plugins on Android.
9. [Custom Native iOS Code](https://capacitorjs.com/docs/ios/custom-code) - Guide to creating and registering local plugins on iOS.
10. [Ionic CORS Troubleshooting Guide](https://ionicframework.com/docs/troubleshooting/cors) - Comprehensive guide on CORS behaviors, origins, and native HTTP bypass.
11. [Capacitor Templates Directory](https://capacitorjs.com/docs/getting-started/templates) - Official list of starter projects for React, SolidJS, and Remix.
12. [Capacitor Issue #4029](https://github.com/ionic-team/capacitor/issues/4029) - GitHub discussion on `webDir` detection and asset copy failures.
13. [Capacitor Issue #6936](https://github.com/ionic-team/capacitor/issues/6936) - GitHub bug report regarding Android custom scheme origin truncation.
