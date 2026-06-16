// Migrated Capacitor device reader.
document.addEventListener('DOMContentLoaded', async function () {
  const Device = window.Capacitor?.Plugins?.Device;
  if (!Device) {
    console.warn('Capacitor Device plugin not found.');
    return;
  }

  try {
    const info = await Device.getInfo();
    const id = await Device.getId();
    const battery = await Device.getBatteryInfo();

    const payload = {
      uuid: id.identifier,
      model: info.model,
      platform: info.platform,
      version: info.osVersion,
      manufacturer: info.manufacturer,
      isVirtual: info.isVirtual,
      serial: null,
      batteryLevel: battery.batteryLevel,
      isCharging: battery.isCharging
    };

    const element = document.getElementById('device-info');
    if (element) {
      element.textContent = JSON.stringify(payload, null, 2);
    }
  } catch (err) {
    console.error('Error reading device info:', err);
  }
});
