// Migrated device reader using @capacitor/device.
(async function () {
  const { Device } = await import('@capacitor/device');

  const [info, id, battery] = await Promise.all([
    Device.getInfo(),
    Device.getId(),
    Device.getBatteryInfo()
  ]);

  const payload = {
    uuid: id.identifier,
    model: info.model,
    platform: info.platform,
    version: info.osVersion,
    manufacturer: info.manufacturer,
    isVirtual: info.isVirtual,
    batteryLevel: battery.batteryLevel,
    isCharging: battery.isCharging
  };

  document.getElementById('device-info').textContent = JSON.stringify(payload, null, 2);
})();