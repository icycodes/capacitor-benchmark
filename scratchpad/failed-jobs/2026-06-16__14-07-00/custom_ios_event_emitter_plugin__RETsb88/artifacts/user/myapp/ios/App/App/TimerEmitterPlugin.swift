import Foundation
import Capacitor

@objc(TimerEmitterPlugin)
public class TimerEmitterPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "TimerEmitterPlugin"
    public let jsName = "TimerEmitter"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "startTimer", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "stopTimer", returnType: CAPPluginReturnPromise),
    ]

    private var timer: Timer?
    private var tickCount: Int = 0

    @objc func startTimer(_ call: CAPPluginCall) {
        let intervalMs = call.getInt("intervalMs") ?? 1000
        let intervalSeconds = Double(intervalMs) / 1000.0

        // Invalidate any existing timer to avoid leaking it
        timer?.invalidate()
        timer = nil
        tickCount = 0

        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            self.timer = Timer.scheduledTimer(withTimeInterval: intervalSeconds, repeats: true) { [weak self] _ in
                guard let self = self else { return }
                self.tickCount += 1
                let n = self.tickCount
                self.notifyListeners("tick", data: ["count": n])
            }
            RunLoop.main.add(self.timer!, forMode: .common)
            call.resolve()
        }
    }

    @objc func stopTimer(_ call: CAPPluginCall) {
        timer?.invalidate()
        timer = nil
        tickCount = 0
        call.resolve()
    }
}
