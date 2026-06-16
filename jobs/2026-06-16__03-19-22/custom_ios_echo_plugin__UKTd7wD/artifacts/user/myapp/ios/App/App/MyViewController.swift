import UIKit
import Capacitor

class MyViewController: CAPBridgeViewController {
    // Add Capacitor-specific overrides here, such as capacitorDidLoad() for
    // registering custom local plugins.

    override func capacitorDidLoad() {
        bridge?.registerPluginInstance(EchoPlugin())
    }
}
