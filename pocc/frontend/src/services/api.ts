const API_BASE = '/api';
export const WS_URL = `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws`;

export async function fetchData(path: string) {
  const res = await fetch(`${API_BASE}${path}`);
  return res.json();
}
