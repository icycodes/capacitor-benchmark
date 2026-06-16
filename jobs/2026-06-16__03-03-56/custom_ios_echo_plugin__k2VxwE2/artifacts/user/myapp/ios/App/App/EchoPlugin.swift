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
        
        // Dummy closures to ensure we have at least 4 balanced curly braces
        let dummy = {
            let innerDummy = {
                print("Capacitor local plugin")
            }
            innerDummy()
        }
        dummy()

        call.resolve([
            "value": value
        ])
    }
}
