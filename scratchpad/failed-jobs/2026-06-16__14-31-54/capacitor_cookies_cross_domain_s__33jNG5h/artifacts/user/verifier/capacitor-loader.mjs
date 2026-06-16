// Resolver hook that maps `@capacitor/core` to our in-process shim.
const SHIM_URL = new URL('./capacitor-core-shim.mjs', import.meta.url).href;

export async function resolve(specifier, context, nextResolve) {
  if (specifier === '@capacitor/core') {
    return { url: SHIM_URL, shortCircuit: true, format: 'module' };
  }
  return nextResolve(specifier, context);
}
