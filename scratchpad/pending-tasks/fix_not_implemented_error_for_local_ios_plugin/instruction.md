In modern Capacitor (v6+), automatic runtime scanning of local native iOS classes was removed to optimize app startup time. As a result, calling a newly created local Swift plugin from JavaScript throws an `Error: "EchoPlugin" plugin is not implemented on ios`.

You need to modify `ios/App/App/MainViewController.swift` to manually register the existing `EchoPlugin` Swift class with the Capacitor bridge.

**Constraints:**
- Must subclass `CAPBridgeViewController` and correctly override the `capacitorDidLoad()` method.
- Must invoke the superclass method and use the native `bridge` object to register the plugin class.