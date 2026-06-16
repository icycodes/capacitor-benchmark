// Migrated to Capacitor
document.addEventListener('DOMContentLoaded', async function () {
  try {
    const { Device } = window.Capacitor.Plugins;
    const info = await Device.getInfo();
    const id = await Device.getId();
    const battery = await Device.getBatteryInfo();

    var payload = {
      uuid: id.identifier,
      model: info.model,
      platform: info.platform,
      version: info.osVersion,
      manufacturer: info.manufacturer,
      isVirtual: info.isVirtual,
      serial: 'unknown',
      batteryLevel: battery.batteryLevel,
      isCharging: battery.isCharging
    };

    document.getElementById('device-info').textContent = JSON.stringify(payload, null, 2);
  } catch (e) {
    document.getElementById('device-info').textContent = 'Error: ' + e.message;
  }
}, false);
