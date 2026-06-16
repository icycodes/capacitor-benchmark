import Capacitor
import Foundation

@objc(TimerEmitterPlugin)
public class TimerEmitterPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "TimerEmitterPlugin"
    public let jsName = "TimerEmitter"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "startTimer", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "stopTimer", returnType: CAPPluginReturnPromise)
    ]

    private var timer: Timer?
    private var count: Int = 0

    @objc func startTimer(_ call: CAPPluginCall) {
        let intervalMs = call.getInt("intervalMs") ?? 1000
        let intervalSeconds = TimeInterval(intervalMs) / 1000.0

        // Invalidate any existing timer to prevent leaks
        timer?.invalidate()

        count = 0

        DispatchQueue.main.async {
            self.timer = Timer.scheduledTimer(withTimeInterval: intervalSeconds, repeats: true) { [weak self] _ in
                guard let self = self else { return }
                self.count += 1
                self.notifyListeners("tick", data: ["count": self.count])
            }
        }

        call.resolve()
    }

    @objc func stopTimer(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            self.timer?.invalidate()
            self.timer = nil
            self.count = 0
        }
        call.resolve()
    }
}