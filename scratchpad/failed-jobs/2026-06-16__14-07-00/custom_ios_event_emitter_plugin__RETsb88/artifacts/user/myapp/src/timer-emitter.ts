import { registerPlugin } from '@capacitor/core';
import type { PluginListenerHandle } from '@capacitor/core';

export interface TickEventData {
  count: number;
}

export interface TimerEmitterPlugin {
  startTimer(options: { intervalMs: number }): Promise<void>;
  stopTimer(): Promise<void>;
  addListener(
    eventName: 'tick',
    listenerFunc: (data: TickEventData) => void
  ): Promise<PluginListenerHandle>;
}

const TimerEmitter = registerPlugin<TimerEmitterPlugin>('TimerEmitter');

export default TimerEmitter;
