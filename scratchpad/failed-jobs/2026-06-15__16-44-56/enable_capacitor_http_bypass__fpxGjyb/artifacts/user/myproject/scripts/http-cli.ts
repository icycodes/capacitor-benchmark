import { CapacitorHttp } from '@capacitor/core';
import type { HttpOptions } from '@capacitor/core';

function parseArgs(argv: string[]): {
  method: string;
  url: string;
  body?: string;
  header?: string;
} {
  let method = '';
  let url = '';
  let body: string | undefined;
  let header: string | undefined;

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--method' && i + 1 < argv.length) {
      method = argv[++i];
    } else if (arg === '--url' && i + 1 < argv.length) {
      url = argv[++i];
    } else if (arg === '--body' && i + 1 < argv.length) {
      body = argv[++i];
    } else if (arg === '--header' && i + 1 < argv.length) {
      header = argv[++i];
    }
  }

  if (!method) {
    throw new Error('--method is required');
  }
  if (!url) {
    throw new Error('--url is required');
  }

  return { method: method.toUpperCase(), url, body, header };
}

async function main(): Promise<void> {
  const { method, url, body, header } = parseArgs(process.argv);

  const headers: Record<string, string> = {};
  if (header) {
    const colonIndex = header.indexOf(':');
    if (colonIndex === -1) {
      throw new Error(`Invalid header format: "${header}". Expected "Name:Value".`);
    }
    const name = header.substring(0, colonIndex).trim();
    const value = header.substring(colonIndex + 1).trim();
    headers[name] = value;
  }

  const options: HttpOptions = {
    url,
    headers,
  };

  if (body !== undefined) {
    options.data = JSON.parse(body);
  }

  let response;

  switch (method) {
    case 'GET':
      response = await CapacitorHttp.get(options);
      break;
    case 'POST':
      response = await CapacitorHttp.post(options);
      break;
    default:
      options.method = method;
      response = await CapacitorHttp.request(options);
      break;
  }

  console.log(`Status: ${response.status}`);
  console.log(JSON.stringify(response.data));
}

main().catch((err: unknown) => {
  console.error(err);
  process.exit(1);
});