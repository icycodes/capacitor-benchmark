# Implement a Stateful Counter Capacitor Android Plugin

## Background
You are working on a Capacitor v8 hybrid mobile application located at `/home/user/myapp`. The project already has the `android` platform scaffolded at `/home/user/myapp/android` and a minimal web frontend in `/home/user/myapp/dist`. The product team wants a small "interaction counter" exposed as a native plugin so the same in-memory counter value is shared across multiple WebView calls and stays consistent regardless of how many JavaScript callers touch it concurrently.

Your job is to design and implement a custom local Capacitor plugin (Java, inside the existing Android project) that owns an in-memory integer counter, exposes it to JavaScript through a thread-safe API, registers it in `MainActivity`, and wires the JavaScript-side bindings so the project compiles cleanly through Gradle.

## Requirements
- Implement a custom local Android Capacitor plugin written in Java inside the existing Android project (do **not** create a separate Capacitor plugin npm package).
- The plugin must be exposed to JavaScript under the exact name `Counter`.
- The plugin must declare three methods that are reachable from JavaScript, each resolving with a JSON object that contains the current counter value under the `value` key:
  - `increment()` — atomically adds one to the counter, then resolves with `{ value: <new value> }`.
  - `decrement()` — atomically subtracts one from the counter, then resolves with `{ value: <new value> }`.
  - `get()` — resolves with `{ value: <current value> }` without changing the counter.
- The counter must start at `0` and survive subsequent calls within the same plugin instance.
- The internal state must use `java.util.concurrent.atomic.AtomicInteger` so concurrent JavaScript callers cannot observe torn updates.
- Register the plugin in the existing `MainActivity` so it is loaded by the Capacitor bridge at startup.
- Provide a TypeScript binding file at `/home/user/myapp/src/counter.ts` that uses `registerPlugin` from `@capacitor/core` to expose the plugin under the name `"Counter"` and exports the plugin object as the default export.
- The complete Android project must compile successfully with the Gradle wrapper.

## Implementation Hints
- Refer to the official Capacitor v8 "Custom Native Android Code" guide. The plugin class must extend `com.getcapacitor.Plugin` and be annotated with `@CapacitorPlugin(name = "Counter")`. Each exposed method must be annotated with `@PluginMethod`.
- Use `JSObject` to build the response object and `call.resolve(...)` to return it to JavaScript.
- The plugin's Java package must match the application package (`com.example.myapp`); place the source under `android/app/src/main/java/com/example/myapp/` so the existing Gradle source set picks it up.
- Use `AtomicInteger` (from `java.util.concurrent.atomic`) as a `private final` field initialized to `0` for the counter state, and rely on its `incrementAndGet`, `decrementAndGet`, and `get` methods.
- Register the plugin with `registerPlugin(MyPlugin.class)` inside `MainActivity.onCreate`.
- On the JavaScript side, the first argument to `registerPlugin` must match the `name` attribute of the `@CapacitorPlugin` annotation exactly.
- The web frontend already has `@capacitor/core` installed as an npm dependency; you do not need to install additional packages.
- The Android SDK, JDK, and the Gradle wrapper are pre-installed and pre-warmed inside the project; running `./gradlew` from `/home/user/myapp/android` will compile the project. Use the `--offline` flag whenever possible to avoid re-downloading dependencies.

## Acceptance Criteria
- Project path: `/home/user/myapp`
- The Android project at `/home/user/myapp/android` must build successfully via:
  - `cd /home/user/myapp/android && ./gradlew :app:assembleDebug --offline`
- A Java source file implementing the plugin must exist at `/home/user/myapp/android/app/src/main/java/com/example/myapp/CounterPlugin.java`. The file must:
  - Declare `package com.example.myapp;`.
  - Import `com.getcapacitor.Plugin`, `com.getcapacitor.PluginCall`, `com.getcapacitor.PluginMethod`, `com.getcapacitor.JSObject`, `com.getcapacitor.annotation.CapacitorPlugin`, and `java.util.concurrent.atomic.AtomicInteger`.
  - Annotate the class with `@CapacitorPlugin(name = "Counter")`.
  - Declare a class named `CounterPlugin` that `extends Plugin`.
  - Contain a `private final AtomicInteger` field initialized to `0`.
  - Declare three `@PluginMethod`-annotated methods named `increment`, `decrement`, and `get`, each accepting `PluginCall` and calling `call.resolve(...)` with a `JSObject` containing the current `value`.
- `MainActivity` at `/home/user/myapp/android/app/src/main/java/com/example/myapp/MainActivity.java` must contain a `registerPlugin(CounterPlugin.class)` call placed inside `onCreate(Bundle savedInstanceState)`.
- A TypeScript binding file must exist at `/home/user/myapp/src/counter.ts` that imports `registerPlugin` from `@capacitor/core`, registers a plugin under the exact string literal `"Counter"`, and provides a default export.
- The compiled debug APK produced at `/home/user/myapp/android/app/build/outputs/apk/debug/app-debug.apk` must contain the `CounterPlugin` class in its DEX (verifiable by listing classes inside the APK).

