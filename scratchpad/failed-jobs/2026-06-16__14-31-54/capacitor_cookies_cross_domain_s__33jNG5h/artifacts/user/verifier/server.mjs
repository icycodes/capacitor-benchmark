// Tiny fixture HTTP server used by the behavioral verifier.
// Routes:
//   POST /login   -> 200 with {session_id, user} and Set-Cookie on success; 401 otherwise.
//   GET  /whoami  -> 200 with {user:'alice'} if cookie session_id=SESSION_TOKEN present; 401 otherwise.
import http from 'node:http';

export function startFixtureServer() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const chunks = [];
      req.on('data', (c) => chunks.push(c));
      req.on('end', () => {
        const body = Buffer.concat(chunks).toString('utf-8');
        const url = req.url || '/';
        if (req.method === 'POST' && url === '/login') {
          let payload = {};
          try { payload = JSON.parse(body || '{}'); } catch { payload = {}; }
          if (payload && payload.user === 'alice' && payload.pass === 'wonderland') {
            res.statusCode = 200;
            res.setHeader('Content-Type', 'application/json');
            res.setHeader('Set-Cookie', 'session_id=SESSION_TOKEN; Path=/');
            res.end(JSON.stringify({ session_id: 'SESSION_TOKEN', user: 'alice' }));
            return;
          }
          res.statusCode = 401;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: 'bad credentials' }));
          return;
        }
        if (req.method === 'GET' && url === '/whoami') {
          const cookie = req.headers.cookie || '';
          if (cookie.split(';').map((s) => s.trim()).some((c) => c === 'session_id=SESSION_TOKEN')) {
            res.statusCode = 200;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({ user: 'alice' }));
            return;
          }
          res.statusCode = 401;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: 'unauthenticated' }));
          return;
        }
        res.statusCode = 404;
        res.end();
      });
    });
    server.listen(0, '127.0.0.1', () => {
      const addr = server.address();
      const port = typeof addr === 'object' && addr ? addr.port : 0;
      resolve({ server, port });
    });
  });
}

if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  startFixtureServer().then(({ port }) => {
    console.log(`fixture listening on 127.0.0.1:${port}`);
  });
}
