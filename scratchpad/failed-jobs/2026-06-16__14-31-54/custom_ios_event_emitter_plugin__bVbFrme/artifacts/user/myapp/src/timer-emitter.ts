import { registerPlugin } from '@capacitor/core';

export interface TickEvent {
  count: number;
}

export interface TimerEmitterPlugin {
  startTimer(options: { intervalMs: number }): Promise<void>;
  stopTimer(): Promise<void>;
  addListener(eventName: 'tick', listenerFunc: (event: TickEvent) => void): Promise<any>;
}

const TimerEmitter = registerPlugin<TimerEmitterPlugin>('TimerEmitter');

export default TimerEmitter;