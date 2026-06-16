import { registerPlugin, PluginListenerHandle } from '@capacitor/core';

export interface CounterResult {
  value: number;
}

export interface CounterChangeEvent {
  value: number;
}

export interface CounterPlugin {
  increment(options?: Record<string, never>): Promise<CounterResult>;
  reset(options?: Record<string, never>): Promise<CounterResult>;
  getValue(options?: Record<string, never>): Promise<CounterResult>;
  addListener(
    eventName: 'change',
    listenerFunc: (event: CounterChangeEvent) => void,
  ): Promise<PluginListenerHandle>;
}

const Counter = registerPlugin<CounterPlugin>('Counter');

export default Counter;
