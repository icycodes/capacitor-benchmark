// Migrated device reader — uses @capacitor/device instead of the legacy
// Cordova device plugin.
import { Device } from '@capacitor/device';

async function loadDeviceInfo() {
  try {
    const [info, id, battery] = await Promise.all([
      Device.getInfo(),
      Device.getId(),
      Device.getBatteryInfo(),
    ]);

    const payload = {
      model: info.model,
      platform: info.platform,
      operatingSystem: info.operatingSystem,
      osVersion: info.osVersion,
      manufacturer: info.manufacturer,
      isVirtual: info.isVirtual,
      webViewVersion: info.webViewVersion,
      identifier: id.identifier,
      batteryLevel: battery.batteryLevel,
      isCharging: battery.isCharging,
    };

    document.getElementById('device-info').textContent =
      JSON.stringify(payload, null, 2);
  } catch (err) {
    document.getElementById('device-info').textContent =
      'Error loading device info: ' + err.message;
  }
}

loadDeviceInfo();
