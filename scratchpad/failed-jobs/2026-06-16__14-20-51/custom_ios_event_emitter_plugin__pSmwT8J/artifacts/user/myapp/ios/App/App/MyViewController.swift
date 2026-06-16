import UIKit
import Capacitor

class MyViewController: CAPBridgeViewController {
    override func capacitorDidLoad() {
        super.capacitorDidLoad()
        bridge?.registerPluginInstance(TimerEmitterPlugin())
    }
}
