# Capacitor Benchmark Research Plan & Dataset Specification

This document provides a highly structured, technically rigorous research report on **Capacitor** (by Ionic), tailored for creating high-quality evaluation datasets and benchmark tasks for AI coding agents.

---

## 1. Library Overview

### Description
**Capacitor** is an open-source, cross-platform native runtime designed by Ionic. It enables developers to build modern, high-performance hybrid mobile applications for iOS and Android, as well as Progressive Web Apps (PWAs), using standard web technologies (HTML, CSS, JavaScript/TypeScript). Unlike Cordova, which abstracts the native platforms away, Capacitor treats the native iOS and Android projects as source-controlled build targets, providing direct access to native SDKs and allowing developers to write custom native code alongside web-based frontend frameworks.

### Ecosystem Role
Capacitor bridges the gap between web development and native mobile development. It acts as an "Electron for mobile," hosting a native WebView (`WKWebView` on iOS, `WebView` on Android) and providing a unified, typed JavaScript/TypeScript API to access native hardware (e.g., Camera, Geolocation, Filesystem, Biometrics). It is compatible with any modern frontend framework (such as React, Vue, Angular, Svelte, or SolidJS) and integrates seamlessly with bundlers/compilers (Vite, Next.js, Webpack).

### Project Setup (Non-Interactive CLI Instructions)
To integrate Capacitor into an existing web project programmatically (e.g., inside a non-interactive Docker container or CI environment), avoid the interactive prompts of `npx cap init` by supplying explicit CLI arguments and flags:

1. **Install Core Dependencies**:
   Install the core runtime and CLI utility as development dependencies:
   ```bash
   npm install @capacitor/core
   npm install --save-dev @capacitor/cli
   ```

2. **Initialize Capacitor (Non-Interactive)**:
   Initialize the project configuration by passing the App Name, App ID (Package Name/Bundle Identifier), and the web asset build directory (e.g., `dist` or `out`):
   ```bash
   npx cap init "My Capacitor App" "com.example.myapp" --web-dir dist
   ```
   *Note: This command creates a `capacitor.config.ts` (or `capacitor.config.json`) file in the project root.*

3. **Install Native Platform Packages**:
   Install the native platform packages for iOS and Android:
   ```bash
   npm install @capacitor/android @capacitor/ios
   ```

4. **Add Platforms to the Project**:
   Generate the native iOS and Android project directories:
   ```bash
   npx cap add android
   npx cap add ios
   ```

5. **Sync Web Assets & Plugins**:
   Compile the web application (e.g., `npm run build`) and copy the built assets into the native platform projects while updating native dependencies:
   ```bash
   npx cap sync
   ```

---

## 2. Core Primitives & APIs

The Capacitor ecosystem consists of three primary runtime/API surfaces:
1. **The Capacitor Bridge**: The core native layer connecting JavaScript to Swift (iOS) and Kotlin/Java (Android).
2. **Capacitor Core JS Utilities**: Utilities provided by `@capacitor/core` to manage platform detection and file path translation.
3. **Plugins**: Modular units of native functionality exposed to the web layer.

### Key Primitives and Documentation Links
* [Capacitor Configuration](https://capacitorjs.com/docs/config): High-level options for the Capacitor CLI and runtime.
* [Capacitor JS Utilities](https://capacitorjs.com/docs/basics/utilities): Core runtime utilities (`getPlatform`, `isNativePlatform`, `convertFileSrc`).
* [Custom Native iOS Code](https://capacitorjs.com/docs/ios/custom-code): Writing local Swift plugins for iOS using `CAPBridgedPlugin` (Capacitor 6/7/8).
* [Custom Native Android Code](https://capacitorjs.com/docs/android/custom-code): Writing local Kotlin/Java plugins for Android using `@CapacitorPlugin`.
* [Official Core Plugins](https://capacitorjs.com/docs/plugins): Essential hardware APIs (Camera, Filesystem, Device, Geolocation).

---

### Detailed Primitives & Code Snippets

#### Concept 1: Core JS Utilities (`Capacitor` Object)
Developers use the `Capacitor` utility object to adapt code depending on whether it runs in a browser or inside a native WebView, and to translate native file paths into URLs that can be loaded securely in the WebView.

##### TypeScript/JavaScript Snippet:
```typescript
import { Capacitor } from '@capacitor/core';

// 1. Detect platform and native environment
const platform = Capacitor.getPlatform(); // 'ios' | 'android' | 'web'
const isNative = Capacitor.isNativePlatform(); // true if running in iOS/Android WebView

console.log(`Running on ${platform} (Native: ${isNative})`);

// 2. Convert a native file URI (e.g., file://...) to a Web View-friendly URL
// Critical for displaying captured photos/videos in <img src="..."> or <video src="...">
const nativeFileUri = 'file:///var/mobile/Containers/Data/Application/.../tmp/photo.jpg';
const webViewFriendlyUrl = Capacitor.convertFileSrc(nativeFileUri);

// Result: 'http://localhost/_capacitor_file_/var/mobile/Containers/Data/Application/.../tmp/photo.jpg' (Android)
// or 'capacitor://localhost/_capacitor_file_/var/mobile/Containers/Data/Application/.../tmp/photo.jpg' (iOS)
const imgElement = document.getElementById('preview') as HTMLImageElement;
if (imgElement) {
  imgElement.src = webViewFriendlyUrl;
}
```

---

#### Concept 2: Custom Local Native Plugins (Capacitor 6/7/8 Specification)
Capacitor allows developers to write native code (Swift on iOS, Kotlin on Android) and invoke it from JavaScript with full TypeScript type safety. In modern Capacitor (v6+), iOS custom plugins no longer require an Objective-C `.m` file; they conform to `CAPBridgedPlugin` directly in Swift.

##### 1. TypeScript Interface & Bridge Registration (`src/plugins/EchoPlugin.ts`)
```typescript
import { registerPlugin } from '@capacitor/core';

export interface EchoPlugin {
  echo(options: { value: string }): Promise<{ value: string }>;
}

// Register the plugin with the Capacitor bridge
const Echo = registerPlugin<EchoPlugin>('Echo');
export default Echo;
```

##### 2. iOS Swift Native Implementation (`ios/App/App/EchoPlugin.swift`)
```swift
import Foundation
import Capacitor

@objc(EchoPlugin)
public class EchoPlugin: CAPPlugin, CAPBridgedPlugin {
    // Required properties for CAPBridgedPlugin (Capacitor 6/7/8)
    public let identifier = "EchoPlugin"
    public let jsName = "Echo"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "echo", returnType: CAPPluginReturnPromise)
    ]

    @objc func echo(_ call: CAPPluginCall) {
        let value = call.getString("value") ?? ""
        
        // Resolve the promise and return data to the WebView
        call.resolve([
            "value": value
        ])
    }
}
```

##### 3. iOS Manual Plugin Registration (`ios/App/App/MainViewController.swift`)
Because automatic scanning of local plugins was removed in Capacitor 6, local plugins must be registered manually in the View Controller:
```swift
import UIKit
import Capacitor

class MainViewController: CAPBridgeViewController {
    override open func capacitorDidLoad() {
        super.capacitorDidLoad()
        // Register the local custom plugin class
        bridge?.registerPlugin(EchoPlugin.self)
    }
}
```

##### 4. Android Kotlin Native Implementation (`android/app/src/main/java/com/example/myapp/EchoPlugin.kt`)
```kotlin
package com.example.myapp

import com.getcapacitor.JSObject
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.CapacitorPlugin

@CapacitorPlugin(name = "Echo")
class EchoPlugin : Plugin() {

    @PluginMethod
    fun echo(call: PluginCall) {
        val value = call.getString("value") ?: ""
        
        val ret = JSObject()
        ret.put("value", value)
        
        // Resolve the promise and return data to the WebView
        call.resolve(ret)
    }
}
```

##### 5. Android Manual Plugin Registration (`android/app/src/main/java/com/example/myapp/MainActivity.kt`)
```kotlin
package com.example.myapp

import android.os.Bundle
import com.getcapacitor.BridgeActivity

class MainActivity : BridgeActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        // Register the local custom plugin before super.onCreate()
        registerPlugin(EchoPlugin::class.java)
        super.onCreate(savedInstanceState)
    }
}
```

##### 6. Calling the Plugin from Web Code
```typescript
import Echo from './plugins/EchoPlugin';

async function testNativeBridge() {
  try {
    const response = await Echo.echo({ value: 'Hello from JavaScript!' });
    console.log('Native response:', response.value); // 'Hello from JavaScript!'
  } catch (error) {
    console.error('Failed to call native code:', error);
  }
}
```

---

## 3. Real-World Use Cases & Templates

### Templates & Showcases
* [Next.js + Tailwind + Ionic Starter](https://github.com/mlynch/nextjs-tailwind-ionic-capacitor-starter): A conceptual starting point for hybrid apps combining Next.js App Router, Tailwind CSS, and Capacitor.
* [Capacitor SolidJS + Vite Templates](https://github.com/ionic-team/capacitor-solidjs-templates): Official production-ready starter templates for SolidJS and Vite.
* [SwapLab Capacitor Multi-Framework Templates](https://github.com/swaplab-engine/template-capacitor): Pre-configured, modern templates for Angular, React (Vite), SolidJS, and Next.js, tailored for automated build pipelines.

### Common Integration Patterns
* **Monorepo Architecture (Vite Frontend + Next.js Backend)**:
  A highly productive pattern featuring a monorepo (using npm/pnpm workspaces or TurboRepo) where the mobile app lives in `apps/mobile` (built with Vite + React + Capacitor) and a backend API lives in `apps/api` (Next.js). This ensures ultra-fast HMR during development and clean logical separation.
* **Static Site Generation (SSG) for Production**:
  Since Capacitor hosts the web app inside a native WebView, traditional Node.js Server-Side Rendering (SSR) is not possible on-device. Frameworks like Next.js must be configured for static exports (`output: 'export'` in `next.config.js`), outputting to a static directory (e.g., `out`), which is then referenced in `capacitor.config.ts` as `webDir: 'out'`.

---

## 4. Developer Friction Points

### Friction Point 1: Custom Local Plugins Throwing "Not Implemented" on iOS
* **Symptom**: After upgrading to Capacitor 6, 7, or 8, calling a custom local native iOS plugin throws:
  `Error: "PluginName" plugin is not implemented on ios`
* **Underlying Cause**: To optimize application startup performance, Capacitor 6 removed the automatic runtime scanning of local native iOS classes. Only plugins installed as npm packages are auto-discovered. Local Swift classes are ignored by default.
* **Resolution**: Developers must manually register local Swift plugins. This is achieved by subclassing `CAPBridgeViewController` (e.g., `MainViewController.swift`), overriding `capacitorDidLoad()`, and registering the plugin class via `bridge?.registerPlugin(MyPlugin.self)`. Alternatively, in Capacitor 7/8, it can be registered statically in `CAPPluginRegistrant.swift`.
* **Reference**: [GitHub Issue #7443 - Local plugins showing as not implemented](https://github.com/ionic-team/capacitor/issues/7443)

### Friction Point 2: CORS Violations with Custom Native Schemes
* **Symptom**: Standard web `fetch` or `axios` requests to external APIs fail with CORS errors:
  `Origin capacitor://localhost is not allowed by Access-Control-Allow-Origin`
* **Underlying Cause**: Inside the native WebView, Capacitor serves the web bundle under a custom security scheme (`capacitor://localhost` on iOS, `http://localhost` on Android) to bypass sandboxing restrictions. External servers or OAuth providers often reject these non-standard origins because they only whitelist standard `http://` or `https://` origins.
* **Resolution**:
  1. Add `capacitor://localhost` and `http://localhost` to the backend API's CORS configuration.
  2. Alternatively, enable the native HTTP plugin (`CapacitorHttp` in `capacitor.config.ts`). This intercepts browser-level HTTP requests and routes them through native iOS/Android networking libraries, which are not subject to browser-level CORS restrictions.
* **Reference**: [Capacitor Configuration Guide - CORS & CapacitorHttp](https://capacitorjs.com/docs/config)

---

## 5. Evaluation Ideas

The following high-level concepts can be expanded into concrete coding tasks for testing AI agents on Capacitor proficiency:

### Simple Tier
1. **Initialize and Configure Capacitor in a Vite/React App**: Add Capacitor to an existing Vite-based React project, configure the correct output build directory, and initialize the configuration file.
2. **Implement Device Battery and Network Status Monitoring**: Build a component that uses the official `@capacitor/device` and `@capacitor/network` plugins to display the real-time battery level and network status of the device.

### Medium Tier
3. **Build a Native Photo Gallery with Local Storage Persistence**: Use `@capacitor/camera` to capture photos, write them to persistent native storage using `@capacitor/filesystem`, and store their native paths in `@capacitor/preferences`.
4. **Create a Custom Local Native Bridge Plugin**: Write a custom local plugin in Swift (iOS) and Kotlin (Android) that returns hardware-specific metadata, and manually register it on both platforms.

### Complex Tier
5. **Implement Biometric Authentication and Secure Credential Storage**: Build a secure login flow that utilizes biometric authentication (FaceID/TouchID) and stores auth tokens in the device's secure enclave.
6. **Set up Background Geolocation Tracking with Local Push Notifications**: Implement a geofencing feature that tracks coordinates in the background and triggers a native local notification when entering or leaving a specified region.

---

## 6. Sources

1. [Capacitor Official Website](https://capacitorjs.com): The main landing page for the Capacitor cross-platform runtime.
2. [Capacitor Installation Guide](https://capacitorjs.com/docs/getting-started): Official guide detailing installation and initialization using the CLI.
3. [Capacitor Configuration Reference](https://capacitorjs.com/docs/config): Detailed documentation on `capacitor.config.ts` options.
4. [Capacitor iOS Custom Native Code Guide](https://capacitorjs.com/docs/ios/custom-code): Official documentation on creating local iOS plugins and manual registration.
5. [Capacitor Android Custom Native Code Guide](https://capacitorjs.com/docs/android/custom-code): Official documentation on creating local Android plugins and registering them in `MainActivity`.
6. [Capacitor JS Utilities Reference](https://capacitorjs.com/docs/basics/utilities): Official API documentation for `Capacitor` object methods.
7. [GitHub Issue #7443 - iOS Local Plugins Not Implemented](https://github.com/ionic-team/capacitor/issues/7443): Developer discussion explaining why local Swift plugins require manual registration in Capacitor 6+.
8. [Capacitor Live Reload Guide](https://capacitorjs.com/docs/guides/live-reload): Detailed steps for setting up live reload and handling cleartext traffic.
9. [Announcing Capacitor 8 - Ionic Blog](https://ionic.io/blog/announcing-capacitor-8): Official announcement detailing Capacitor 8 releases, support policies, and dependency updates.
