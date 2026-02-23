// API Client Library

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

// Get token from cookies
function getAuthHeader(): Record<string, string> {
  if (typeof document === 'undefined') return {};
  const token = document.cookie
    .split('; ')
    .find(row => row.startsWith('access_token='))
    ?.split('=')[1];
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {} } = options;

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
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
    const token = document.cookie
      .split('; ')
      .find(row => row.startsWith('access_token='))
      ?.split('=')[1];

    return fetch(`${API_BASE}/api/chat/${agentId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
  },

  getSessions: (agentId: string) =>
    request<import('@/types').ChatSession[]>(`/api/chat/${agentId}/sessions`),

  getSession: (agentId: string, sessionId: string) =>
    request<import('@/types').ChatSession>(`/api/chat/${agentId}/sessions/${sessionId}`),
};

// Experiments API
export const experimentsApi = {
  list: (params?: { agent_id?: string; experiment_type?: string; status?: string }) => {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return request<import('@/types').Experiment[]>(`/api/experiments${query ? `?${query}` : ''}`);
  },

  create: (data: import('@/types').CreateExperimentRequest) =>
    request<import('@/types').Experiment>('/api/experiments', {
      method: 'POST',
      body: data,
    }),

  get: (id: string) => request<import('@/types').Experiment>(`/api/experiments/${id}`),

  update: (id: string, data: Partial<import('@/types').UpdateExperimentRequest>) =>
    request<import('@/types').Experiment>(`/api/experiments/${id}`, {
      method: 'PUT',
      body: data,
    }),

  delete: (id: string) => request<void>(`/api/experiments/${id}`, {
    method: 'DELETE',
  }),

  run: (id: string, input_data?: Record<string, unknown>) =>
    request<import('@/types').Experiment>(`/api/experiments/${id}/run`, {
      method: 'POST',
      body: input_data ? { input_data } : {},
    }),
};

// Templates API
export const templatesApi = {
  list: (params?: { experiment_type?: string }) => {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return request<import('@/types').ExperimentTemplate[]>(`/api/templates${query ? `?${query}` : ''}`);
  },

  create: (data: import('@/types').CreateTemplateRequest) =>
    request<import('@/types').ExperimentTemplate>('/api/templates', {
      method: 'POST',
      body: data,
    }),

  get: (id: string) => request<import('@/types').ExperimentTemplate>(`/api/templates/${id}`),

  delete: (id: string) => request<void>(`/api/templates/${id}`, {
    method: 'DELETE',
  }),
};

// Experiences API
export const experiencesApi = {
  list: (params?: { experiment_id?: string }) => {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return request<import('@/types').ExperimentExperience[]>(`/api/experiences${query ? `?${query}` : ''}`);
  },

  create: (data: import('@/types').CreateExperienceRequest) =>
    request<import('@/types').ExperimentExperience>('/api/experiences', {
      method: 'POST',
      body: data,
    }),

  get: (id: string) => request<import('@/types').ExperimentExperience>(`/api/experiences/${id}`),

  search: (keyword: string) =>
    request<import('@/types').ExperimentExperience[]>(`/api/experiences/search?keyword=${encodeURIComponent(keyword)}`),
};
