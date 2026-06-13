import { CapacitorHttp } from '@capacitor/core';

async function main() {
  const args = process.argv.slice(2);

  let method: string | undefined;
  let url: string | undefined;
  let bodyStr: string | undefined;
  let headerStr: string | undefined;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--method') {
      method = args[i + 1];
      i++;
    } else if (args[i] === '--url') {
      url = args[i + 1];
      i++;
    } else if (args[i] === '--body') {
      bodyStr = args[i + 1];
      i++;
    } else if (args[i] === '--header') {
      headerStr = args[i + 1];
      i++;
    }
  }

  if (!method || !url) {
    console.error('Error: --method and --url are required.');
    process.exit(1);
  }

  const upperMethod = method.toUpperCase();
  if (upperMethod !== 'GET' && upperMethod !== 'POST') {
    console.error('Error: Only GET and POST methods are supported.');
    process.exit(1);
  }

  const headers: Record<string, string> = {};

  // Parse the optional custom header
  if (headerStr) {
    const colonIndex = headerStr.indexOf(':');
    if (colonIndex !== -1) {
      const name = headerStr.slice(0, colonIndex).trim();
      const value = headerStr.slice(colonIndex + 1).trim();
      headers[name] = value;
    }
  }

  // Handle ZEALT_RUN_ID environment variable
  if (process.env.ZEALT_RUN_ID) {
    const runId = process.env.ZEALT_RUN_ID;
    if (!headers['run-id'] && !headers['Run-Id'] && !headers['RUN-ID']) {
      headers['run-id'] = runId;
    }
    if (!headers['x-run-id'] && !headers['X-Run-Id'] && !headers['X-RUN-ID']) {
      headers['X-Run-Id'] = runId;
    }
    if (!headers['zealt-run-id'] && !headers['Zealt-Run-Id'] && !headers['ZEALT-RUN-ID']) {
      headers['zealt-run-id'] = runId;
    }
  }

  let data: any = undefined;
  if (bodyStr) {
    try {
      data = JSON.parse(bodyStr);
    } catch {
      data = bodyStr;
    }

    // Set default Content-Type to application/json for POST request with body
    const hasContentType = Object.keys(headers).some(
      key => key.toLowerCase() === 'content-type'
    );
    if (!hasContentType) {
      headers['Content-Type'] = 'application/json';
    }
  }

  try {
    const response = await CapacitorHttp.request({
      url,
      method: upperMethod,
      headers,
      data,
    });

    let responseBody = response.data;
    if (typeof responseBody === 'string') {
      try {
        responseBody = JSON.parse(responseBody);
      } catch {
        // Keep as string if it's not JSON
      }
    }

    console.log(`Status: ${response.status}`);
    console.log(JSON.stringify(responseBody ?? {}));
  } catch (err: any) {
    console.error('Error making request:', err.message || err);
    process.exit(1);
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
