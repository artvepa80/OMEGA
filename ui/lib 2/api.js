const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function apiGet(path) {
  const res = await fetch(`${BASE}${path}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
  return res.json();
}

export async function apiPost(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {})
  });
  if (!res.ok) {
    let detail = '';
    try { detail = (await res.json()).detail; } catch {}
    throw new Error(`POST ${path} -> ${res.status} ${detail || ''}`);
  }
  return res.json();
}

export function logsWebSocketURL() {
  try {
    const u = new URL(BASE);
    const proto = u.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${u.host}/ws/logs`;
  } catch {
    return 'ws://localhost:8000/ws/logs';
  }
}


