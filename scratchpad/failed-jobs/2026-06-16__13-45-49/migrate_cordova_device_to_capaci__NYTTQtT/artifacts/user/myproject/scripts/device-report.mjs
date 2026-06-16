import './shim.js';
import { Device } from '@capacitor/device';

async function run() {
  try {
    const info = await Device.getInfo();
    const id = await Device.getId();
    const battery = await Device.getBatteryInfo();

    const report = {
      info: {
        platform: info.platform || "web",
        operatingSystem: info.operatingSystem || "unknown",
        osVersion: info.osVersion || "",
        manufacturer: info.manufacturer || "",
        model: info.model || "",
        isVirtual: typeof info.isVirtual === 'boolean' ? info.isVirtual : false,
        webViewVersion: info.webViewVersion || ""
      },
      id: {
        identifier: id.identifier || ""
      },
      battery: {
        batteryLevel: typeof battery.batteryLevel === 'number' ? battery.batteryLevel : 1.0,
        isCharging: typeof battery.isCharging === 'boolean' ? battery.isCharging : true
      }
    };

    console.log(JSON.stringify(report));
  } catch (error) {
    console.error("Error generating device report:", error);
    process.exit(1);
  }
}

run();
