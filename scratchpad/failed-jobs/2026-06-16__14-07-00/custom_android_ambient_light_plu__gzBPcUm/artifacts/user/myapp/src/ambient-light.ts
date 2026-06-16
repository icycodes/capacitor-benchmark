import { registerPlugin } from '@capacitor/core';

export interface AmbientLightPlugin {
  getLightLevel(): Promise<{ value: number }>;
}

const AmbientLight = registerPlugin<AmbientLightPlugin>('AmbientLight');

export default AmbientLight;
