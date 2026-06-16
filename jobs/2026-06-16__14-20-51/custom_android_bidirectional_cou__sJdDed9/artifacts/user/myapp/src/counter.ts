import { registerPlugin, PluginListenerHandle } from '@capacitor/core';

export interface CounterPlugin {
  increment(): Promise<{ value: number }>;
  reset(): Promise<{ value: number }>;
  getValue(): Promise<{ value: number }>;
  addListener(
    eventName: 'change',
    listenerFunc: (state: { value: number }) => void
  ): Promise<PluginListenerHandle> & PluginListenerHandle;
}

const Counter = registerPlugin<CounterPlugin>('Counter');

export default Counter;
