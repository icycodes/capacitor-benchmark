import { CapacitorHttp } from '@capacitor/core';

function parseArgs(): {
  method: string;
  url: string;
  body?: string;
  header?: string;
} {
  const args = process.argv.slice(2);
  const result: ReturnType<typeof parseArgs> = { method: 'GET', url: '' };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--method':
        result.method = args[++i] ?? 'GET';
        break;
      case '--url':
        result.url = args[++i] ?? '';
        break;
      case '--body':
        result.body = args[++i] ?? '';
        break;
      case '--header':
        result.header = args[++i] ?? '';
        break;
    }
  }

  return result;
}

async function main(): Promise<void> {
  const { method, url, body, header } = parseArgs();

  if (!url) {
    process.stderr.write('Error: --url is required\n');
    process.exit(1);
  }

  const headers: Record<string, string> = {};

  if (header) {
    const colonIndex = header.indexOf(':');
    if (colonIndex === -1) {
      process.stderr.write('Error: --header must be in "Name:Value" format\n');
      process.exit(1);
    }
    const name = header.substring(0, colonIndex).trim();
    const value = header.substring(colonIndex + 1).trim();
    if (name && value) {
      headers[name] = value;
    }
  }

  const options: { url: string; method?: string; data?: unknown; headers?: Record<string, string> } = {
    url,
    headers: Object.keys(headers).length > 0 ? headers : undefined,
  };

  if (method.toUpperCase() === 'POST' && body) {
    options.data = body;
  }

  const response = await CapacitorHttp.request({
    ...options,
    method: method.toUpperCase(),
  });

  process.stdout.write(`Status: ${response.status}\n`);
  process.stdout.write(`${JSON.stringify(response.data)}\n`);
}

main().catch((err) => {
  process.stderr.write(`Error: ${err instanceof Error ? err.message : String(err)}\n`);
  process.exit(1);
});
