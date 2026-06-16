import { registerPlugin, PluginListenerHandle } from '@capacitor/core';

export interface TimerEmitterPlugin {
  startTimer(options: { intervalMs: number }): Promise<void>;
  stopTimer(): Promise<void>;
  addListener(
    eventName: 'tick',
    listenerFunc: (event: { count: number }) => void
  ): Promise<PluginListenerHandle> & PluginListenerHandle;
}

const TimerEmitter = registerPlugin<TimerEmitterPlugin>('TimerEmitter');

export default TimerEmitter;
