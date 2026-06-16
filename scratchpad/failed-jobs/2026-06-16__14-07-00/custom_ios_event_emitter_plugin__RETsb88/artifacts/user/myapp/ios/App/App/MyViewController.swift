import UIKit
import Capacitor

class MyViewController: CAPBridgeViewController {
    override func capacitorDidLoad() {
        bridge?.registerPluginInstance(TimerEmitterPlugin())
    }
}
