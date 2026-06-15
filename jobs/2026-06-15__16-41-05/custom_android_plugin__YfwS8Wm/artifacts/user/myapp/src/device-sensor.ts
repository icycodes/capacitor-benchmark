import { registerPlugin } from '@capacitor/core';

export interface DeviceSensorPlugin {
  getReading(options: { sensor: string }): Promise<{ sensor: string; value: number; unit: string }>;
  isAvailable(options: { sensor: string }): Promise<{ available: boolean }>;
}

const DeviceSensor = registerPlugin<DeviceSensorPlugin>("DeviceSensor");

export default DeviceSensor;
