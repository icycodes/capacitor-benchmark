import Foundation
import Capacitor

@objc(TimerEmitterPlugin)
public class TimerEmitterPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "TimerEmitterPlugin"
    public let jsName = "TimerEmitter"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "startTimer", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "stopTimer", returnType: CAPPluginReturnPromise)
    ]

    private var timer: Timer?
    private var counter: Int = 0

    @objc public func startTimer(_ call: CAPPluginCall) {
        let intervalMs = call.getInt("intervalMs") ?? 1000
        let intervalSec = Double(intervalMs) / 1000.0

        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }

            if let existingTimer = self.timer {
                existingTimer.invalidate()
                self.timer = nil
            }

            self.timer = Timer.scheduledTimer(withTimeInterval: intervalSec, repeats: true) { [weak self] _ in
                guard let self = self else { return }
                self.counter += 1
                self.notifyListeners("tick", data: ["count": self.counter])
            }

            call.resolve()
        }
    }

    @objc public func stopTimer(_ call: CAPPluginCall) {
        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }

            if let existingTimer = self.timer {
                existingTimer.invalidate()
                self.timer = nil
            }
            self.counter = 0

            call.resolve()
        }
    }
}
