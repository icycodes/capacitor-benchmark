import { registerPlugin } from '@capacitor/core';

export interface SensorOptions {
  sensor: string;
}

export interface SensorReading {
  sensor: string;
  value: number;
  unit: string;
}

export interface SensorAvailability {
  available: boolean;
}

export interface DeviceSensorPlugin {
  getReading(options: SensorOptions): Promise<SensorReading>;
  isAvailable(options: SensorOptions): Promise<SensorAvailability>;
}

const DeviceSensor = registerPlugin<DeviceSensorPlugin>('DeviceSensor');

export default DeviceSensor;
