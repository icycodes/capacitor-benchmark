import { registerPlugin } from '@capacitor/core';

export interface GetReadingOptions {
  sensor: string;
}

export interface GetReadingResult {
  sensor: string;
  value: number;
  unit: string;
}

export interface IsAvailableOptions {
  sensor: string;
}

export interface IsAvailableResult {
  available: boolean;
}

export interface DeviceSensorPlugin {
  getReading(options: GetReadingOptions): Promise<GetReadingResult>;
  isAvailable(options: IsAvailableOptions): Promise<IsAvailableResult>;
}

const DeviceSensor = registerPlugin<DeviceSensorPlugin>('DeviceSensor');

export default DeviceSensor;
