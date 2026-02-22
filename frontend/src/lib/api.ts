// API Client Library
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {} } = options;

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// Providers API
export const providersApi = {
  list: () => request<import('@/types').LLMProvider[]>('/api/providers'),
  
  create: (data: import('@/types').CreateProviderRequest) =>
    request<import('@/types').LLMProvider>('/api/providers', {
      method: 'POST',
      body: data,
    }),
  
  get: (id: string) => request<import('@/types').LLMProvider>(`/api/providers/${id}`),
  
  update: (id: string, data: Partial<import('@/types').CreateProviderRequest>) =>
    request<import('@/types').LLMProvider>(`/api/providers/${id}`, {
      method: 'PUT',
      body: data,
    }),
  
  delete: (id: string) => request<void>(`/api/providers/${id}`, {
    method: 'DELETE',
  }),
};

// Agents API
export const agentsApi = {
  list: () => request<import('@/types').Agent[]>('/api/agents'),
  
  create: (data: import('@/types').CreateAgentRequest) =>
    request<import('@/types').Agent>('/api/agents', {
      method: 'POST',
      body: data,
    }),
  
  get: (id: string) => request<import('@/types').Agent>(`/api/agents/${id}`),
  
  update: (id: string, data: Partial<import('@/types').CreateAgentRequest>) =>
    request<import('@/types').Agent>(`/api/agents/${id}`, {
      method: 'PUT',
      body: data,
    }),
  
  delete: (id: string) => request<void>(`/api/agents/${id}`, {
    method: 'DELETE',
  }),
};

// Chat API
export const chatApi = {
  sendMessage: (agentId: string, message: string, sessionId?: string) => {
    return fetch(`${API_BASE}/api/chat/${agentId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
  },
  
  getSessions: (agentId: string) =>
    request<import('@/types').ChatSession[]>(`/api/chat/${agentId}/sessions`),
  
  getSession: (agentId: string, sessionId: string) =>
    request<import('@/types').ChatSession>(`/api/chat/${agentId}/sessions/${sessionId}`),
};
