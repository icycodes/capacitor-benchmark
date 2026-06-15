import { CapacitorHttp } from '@capacitor/core';
import type { HttpOptions } from '@capacitor/core';

// ---------------------------------------------------------------------------
// Argument parsing (uses only Node built-ins / process.argv)
// ---------------------------------------------------------------------------

function parseArgs(argv: string[]): {
  method: string;
  url: string;
  body?: string;
  header?: string;
} {
  const args = argv.slice(2); // drop "node" and script path
  const result: { method?: string; url?: string; body?: string; header?: string } = {};

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--method':
        result.method = args[++i];
        break;
      case '--url':
        result.url = args[++i];
        break;
      case '--body':
        result.body = args[++i];
        break;
      case '--header':
        result.header = args[++i];
        break;
      default:
        // ignore unknown flags
        break;
    }
  }

  if (!result.method) {
    console.error('Error: --method is required (GET or POST)');
    process.exit(1);
  }

  if (!result.url) {
    console.error('Error: --url is required');
    process.exit(1);
  }

  return result as { method: string; url: string; body?: string; header?: string };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const { method, url, body, header } = parseArgs(process.argv);

  const headers: Record<string, string> = {};

  // Parse optional "Name:Value" header
  if (header) {
    const colonIndex = header.indexOf(':');
    if (colonIndex === -1) {
      console.error('Error: --header must be in "Name:Value" form');
      process.exit(1);
    }
    const name = header.slice(0, colonIndex).trim();
    const value = header.slice(colonIndex + 1).trim();
    headers[name] = value;
  }

  const options: HttpOptions = {
    url,
    method: method.toUpperCase(),
    headers,
  };

  // Attach body for POST (and other non-GET verbs that carry a payload)
  if (body !== undefined) {
    try {
      options.data = JSON.parse(body);
      // Ensure the server receives valid JSON
      if (!headers['Content-Type'] && !headers['content-type']) {
        headers['Content-Type'] = 'application/json';
      }
    } catch {
      // Treat as plain string if it is not valid JSON
      options.data = body;
    }
  }

  const response = await CapacitorHttp.request(options);

  // Output: exactly two lines
  process.stdout.write(`Status: ${response.status}\n`);
  process.stdout.write(`${JSON.stringify(response.data)}\n`);
}

main().catch((err: unknown) => {
  console.error('Request failed:', err);
  process.exit(1);
});
