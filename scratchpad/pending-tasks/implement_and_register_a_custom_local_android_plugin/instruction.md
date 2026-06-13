To bridge proprietary device features to a web frontend, developers must write custom native Android code using Kotlin and register it with the Capacitor runtime.

You need to create a custom local Android plugin named `EchoPlugin` in Kotlin that reads a string parameter named "value" from a `PluginCall` and resolves the promise with a `JSObject` containing that same string. You must also provide the code to manually register this plugin in `MainActivity.kt`.

**Constraints:**
- The plugin class must extend `Plugin` and be decorated with the `@CapacitorPlugin(name = "Echo")` annotation.
- The manual registration call in `MainActivity.kt` MUST occur before the `super.onCreate(savedInstanceState)` execution.