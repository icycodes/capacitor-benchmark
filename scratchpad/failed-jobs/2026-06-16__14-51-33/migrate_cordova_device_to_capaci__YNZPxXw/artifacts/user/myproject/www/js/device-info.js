// Migrated device reader using @capacitor/device.
(async function () {
  const { Device } = await import('@capacitor/device');

  const [info, id, battery] = await Promise.all([
    Device.getInfo(),
    Device.getId(),
    Device.getBatteryInfo()
  ]);

  var payload = {
    info: info,
    id: id,
    battery: battery
  };

  document.getElementById('device-info').textContent = JSON.stringify(payload, null, 2);
})();
