import { registerPlugin } from '@capacitor/core';

const Echo = registerPlugin<{ echo: (options: { value: string }) => Promise<{ value: string }> }>('Echo');

export default Echo;