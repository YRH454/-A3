const BASE = 'http://localhost:8000/api/v1'

// ---- Auth ----
export async function loginApi(email: string, password: string) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw await res.json()
  return res.json()
}

export async function registerApi(username: string, email: string, password: string) {
  const res = await fetch(`${BASE}/auth/register`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  })
  if (!res.ok) throw await res.json()
  return res.json()
}

export async function guestLoginApi() {
  const res = await fetch(`${BASE}/auth/guest`, { method: 'POST' })
  if (!res.ok) throw await res.json()
  return res.json()
}

// ---- Profile ----
export async function startProfile(userId: number, sessionId?: number) {
  let url = `${BASE}/profile/start?user_id=${userId}`
  if (sessionId) url += `&session_id=${sessionId}`
  const res = await fetch(url, { method: 'POST' })
  if (!res.ok) throw new Error(`Start error: ${res.status}`)
  return res.json()
}

export async function sendMessage(userId: number, message: string, sessionId?: number) {
  const res = await fetch(`${BASE}/profile/chat`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message, session_id: sessionId }),
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function chatWithAgent(userId: number, message: string, onEvent: (data: any) => void) {
  const res = await fetch(`${BASE}/profile/chat/agent`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message }),
  })
  if (!res.ok) throw new Error(`Agent error: ${res.status}`)
  const data = await res.json()
  if (data.events) data.events.forEach(onEvent)
  return data
}

export async function getProfileSessions(userId: number) {
  const res = await fetch(`${BASE}/profile/sessions?user_id=${userId}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function newProfileSession(userId: number) {
  const res = await fetch(`${BASE}/profile/sessions/new?user_id=${userId}`, { method: 'POST' })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

// ---- SSE stream ----
export function streamChat(
  userId: number, message: string,
  onChunk: (data: any) => void, onDone: () => void, onError: (err: Error) => void,
) {
  const url = `${BASE}/profile/chat/stream?user_id=${userId}&message=${encodeURIComponent(message)}`
  const es = new EventSource(url)
  es.onmessage = (e) => {
    if (e.data === '[DONE]') { es.close(); onDone(); return }
    try { onChunk(JSON.parse(e.data)) } catch { /* ignore */ }
  }
  es.onerror = () => { es.close(); onError(new Error('连接中断')) }
  return () => es.close()
}

export async function getProfile(userId: number) {
  const res = await fetch(`${BASE}/profile/${userId}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

// ---- Resources (Multi-Agent Generation) ----

export async function startResourceGeneration(userId: number, message: string, sessionId?: number) {
  const res = await fetch(`${BASE}/resources/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message, session_id: sessionId }),
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function generateResourcesSync(userId: number, message: string, sessionId?: number) {
  const res = await fetch(`${BASE}/resources/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message, session_id: sessionId }),
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export function streamGenerate(
  userId: number, sessionId: number | undefined,
  onEvent: (data: any) => void, onDone: () => void, onError: (err: Error) => void,
) {
  let url = `${BASE}/resources/generate/stream?user_id=${userId}`
  if (sessionId) url += `&session_id=${sessionId}`
  const es = new EventSource(url)
  es.onmessage = (e) => {
    if (e.data === '[DONE]') { es.close(); onDone(); return }
    try { onEvent(JSON.parse(e.data)) } catch { /* ignore */ }
  }
  es.onerror = () => { es.close(); onError(new Error('连接中断')) }
  return () => es.close()
}

export async function getResourceSessions(userId: number) {
  const res = await fetch(`${BASE}/resources/sessions?user_id=${userId}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function newResourceSession(userId: number) {
  const res = await fetch(`${BASE}/resources/sessions/new?user_id=${userId}`, { method: 'POST' })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function getResourcePackage(packageId: number) {
  const res = await fetch(`${BASE}/resources/packages/${packageId}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function listResourcePackages(userId: number) {
  const res = await fetch(`${BASE}/resources/packages?user_id=${userId}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}
