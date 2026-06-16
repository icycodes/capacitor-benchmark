# Upgrade a Capacitor v7 Android Project to Capacitor v8

## Background
A legacy Capacitor 7 application is preinstalled at `/home/user/myapp`. It uses an older Android toolchain (AGP 8.2.1, Gradle 8.2.1, `compileSdkVersion`/`targetSdkVersion` 34, Kotlin 1.9.25) and pins all `@capacitor/*` packages to the `^7.0.0` major. The project must be brought forward to Capacitor 8 end-to-end so that `npx cap sync android` succeeds against the upgraded native toolchain.

## Requirements
- Upgrade every `@capacitor/*` dependency in `package.json` (both `dependencies` and `devDependencies`) to the `^8.0.0` major.
- Update the Android build configuration in `android/build.gradle` to use Android Gradle Plugin `8.7.x` (use a concrete patch version in that line, e.g. `8.7.3`).
- Update `android/gradle/wrapper/gradle-wrapper.properties` so the Gradle distribution URL points at a Gradle `8.11.x` release (e.g. `8.11.1`).
- Raise `compileSdkVersion` and `targetSdkVersion` to `35` in `android/variables.gradle`.
- Update `kotlin_version` in `android/variables.gradle` to `'2.0.21'`.
- Keep `android/app/src/main/java/com/example/myapp/MainActivity.java` valid for Capacitor 8 (`BridgeActivity` subclass) and ensure it still compiles syntactically.
- Install the new JS dependencies and run `npx cap sync android` to validate the upgraded toolchain. The full stdout+stderr of that sync run must be appended to `/home/user/myapp/upgrade.log`.

## Implementation Hints
- The Capacitor 8.0 Upgrade Guide describes which gradle, AGP, Kotlin, and SDK versions are compatible. Translate the high-level guidance into edits to `android/build.gradle`, `android/gradle/wrapper/gradle-wrapper.properties`, and `android/variables.gradle`.
- Run `npm install` (the registry is the public npm mirror; network access is available during the task) so that the new `@capacitor/*` packages and their peers are present before invoking the CLI.
- `npx cap sync android` only inspects JS/native source; it does not require the Android SDK to be installed.
- The project already commits the native `android/` folder per Capacitor conventions, so edit those files in place rather than regenerating the platform.

## Acceptance Criteria
- Project path: /home/user/myapp
- Ensure the upgrade is actually performed and the artifacts exist on disk.
- Log file: /home/user/myapp/upgrade.log
- The log file must contain the marker line `Sync finished` produced by a successful `npx cap sync android` run.
- `package.json` must declare `@capacitor/core`, `@capacitor/cli`, and `@capacitor/android` with version ranges that resolve to the `8.x` major (e.g. `^8.0.0`).
- `android/build.gradle` must reference Android Gradle Plugin `8.7.x` on the `com.android.tools.build:gradle` classpath line.
- `android/gradle/wrapper/gradle-wrapper.properties` must set `distributionUrl` to a Gradle `8.11.x` distribution.
- `android/variables.gradle` must define `compileSdkVersion = 35`, `targetSdkVersion = 35`, and `kotlin_version = '2.0.21'`.
- `android/app/src/main/java/com/example/myapp/MainActivity.java` must remain a `BridgeActivity` subclass and parse as valid Java.
- `node_modules/@capacitor/core/package.json` must report a version satisfying `^8.0.0` (i.e. the v8 packages were actually installed, not just declared).

