import { registerPlugin } from '@capacitor/core';
import type { PluginListenerHandle } from '@capacitor/core';

export interface CounterValue {
  value: number;
}

export interface CounterPlugin {
  increment(): Promise<CounterValue>;
  reset(): Promise<CounterValue>;
  getValue(): Promise<CounterValue>;
  addListener(
    eventName: 'change',
    listenerFunc: (state: CounterValue) => void,
  ): Promise<PluginListenerHandle>;
}

const Counter = registerPlugin<CounterPlugin>('Counter');

export default Counter;
