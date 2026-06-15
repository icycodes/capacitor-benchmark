import { CapacitorHttp } from '@capacitor/core';

async function main() {
  const args = process.argv.slice(2);
  let method = 'GET';
  let url = '';
  let body: any = undefined;
  const headers: Record<string, string> = {};

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--method' && i + 1 < args.length) {
      method = args[i + 1].toUpperCase();
      i++;
    } else if (args[i] === '--url' && i + 1 < args.length) {
      url = args[i + 1];
      i++;
    } else if (args[i] === '--body' && i + 1 < args.length) {
      body = args[i + 1];
      i++;
    } else if (args[i] === '--header' && i + 1 < args.length) {
      const headerStr = args[i + 1];
      const colonIndex = headerStr.indexOf(':');
      if (colonIndex > 0) {
        const key = headerStr.substring(0, colonIndex).trim();
        const value = headerStr.substring(colonIndex + 1).trim();
        headers[key] = value;
      }
      i++;
    }
  }

  if (!url) {
    console.error('URL is required');
    process.exit(1);
  }

  try {
    const options = {
      url,
      headers,
      data: body,
    };

    if (method === 'POST' && body !== undefined) {
      const hasContentType = Object.keys(headers).some(
        (k) => k.toLowerCase() === 'content-type'
      );
      if (!hasContentType) {
        headers['Content-Type'] = 'application/json';
      }
      // If we pass a string to CapacitorHttp and Content-Type is application/json, 
      // the web implementation might try to JSON.stringify it again if we are not careful?
      // Let's parse it so CapacitorHttp handles it natively, which is safer for both web and native
      try {
        options.data = JSON.parse(body);
      } catch (e) {
        // Leave as string if it's not valid JSON
      }
    }

    let response;
    if (method === 'GET') {
      response = await CapacitorHttp.get(options);
    } else if (method === 'POST') {
      response = await CapacitorHttp.post(options);
    } else {
      response = await CapacitorHttp.request({ ...options, method });
    }

    console.log(`Status: ${response.status}`);
    console.log(JSON.stringify(response.data));
  } catch (error) {
    console.error(error);
    process.exit(1);
  }
}

main();
