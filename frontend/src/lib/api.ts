// API Client Library

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

// Get token from localStorage (more reliable in Next.js)
function getAuthHeader(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  const token = localStorage.getItem('token');
  console.log('[API] Token from localStorage:', token ? `${token.substring(0, 20)}...` : 'NOT FOUND');
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

  getDetail: (id: string) => request<import('@/types').AgentDetail>(`/api/agents/${id}/detail`),

  update: (id: string, data: Partial<import('@/types').CreateAgentRequest>) =>
    request<import('@/types').Agent>(`/api/agents/${id}`, {
      method: 'PUT',
      body: data,
    }),

  delete: (id: string) => request<void>(`/api/agents/${id}`, {
    method: 'DELETE',
  }),

  // 能力相关
  getCapabilities: (id: string) =>
    request<import('@/types').AgentCapabilities>(`/api/agents/${id}/capabilities`),

  updateCapabilities: (id: string) =>
    request<import('@/types').AgentCapabilities>(`/api/agents/${id}/capabilities/update`, {
      method: 'POST',
    }),

  previewPrompt: (id: string, taskDescription: string) =>
    request<import('@/types').PromptPreviewResponse>(`/api/agents/${id}/prompt/preview`, {
      method: 'POST',
      body: { task_description: taskDescription },
    }),
};

// Chat API
export const chatApi = {
  sendMessage: (agentId: string, message: string, sessionId?: string) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

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

  // 跨Agent经验查询 - 获取用户所有Agent的经验
  listUserExperiences: (userId: string, params?: { status?: 'verified' | 'draft' | 'deprecated'; limit?: number }) => {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return request<import('@/types').UserExperience[]>(`/api/experiences/user/${userId}${query ? `?${query}` : ''}`);
  },
};

// Soul API
export const soulApi = {
  get: () => request<import('@/types').UserSoul>('/api/soul'),

  update: (data: import('@/types').SoulUpdateRequest) =>
    request<import('@/types').UserSoul>('/api/soul', {
      method: 'POST',
      body: data,
    }),

  getTemplate: () =>
    request<{ soul_content: string; core_truths: string[]; boundaries: string[]; vibe: string }>('/api/soul/template'),
};

// Documents API (Doc Market)
export const documentsApi = {
  list: (params?: { doc_type?: string; category?: string; tags?: string; is_public?: boolean; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.doc_type) searchParams.set('doc_type', params.doc_type);
    if (params?.category) searchParams.set('category', params.category);
    if (params?.tags) searchParams.set('tags', params.tags);
    if (params?.is_public !== undefined) searchParams.set('is_public', String(params.is_public));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    const query = searchParams.toString();
    return request<import('@/types').Document[]>(`/api/market/documents${query ? `?${query}` : ''}`);
  },

  get: (id: string) => request<import('@/types').Document>(`/api/market/documents/${id}`),

  create: (data: import('@/types').CreateDocumentRequest) =>
    request<import('@/types').Document>('/api/market/documents', {
      method: 'POST',
      body: data,
    }),

  upload: (file: File, data: { name: string; doc_type?: string; category?: string; description?: string; tags?: string; is_public?: boolean }) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', data.name);
    if (data.doc_type) formData.append('doc_type', data.doc_type);
    if (data.category) formData.append('category', data.category);
    if (data.description) formData.append('description', data.description);
    if (data.tags) formData.append('tags', data.tags);
    formData.append('is_public', String(data.is_public ?? false));

    return request<import('@/types').Document>('/api/market/documents/upload', {
      method: 'POST',
      body: formData,
    });
  },

  delete: (id: string) => request<void>(`/api/market/documents/${id}`, {
    method: 'DELETE',
  }),

  updateVisibility: (id: string, isPublic: boolean) =>
    request<import('@/types').Document>(`/api/market/documents/${id}/visibility`, {
      method: 'PATCH',
      body: { is_public: isPublic },
    }),

  search: (keyword: string) =>
    request<import('@/types').Document[]>(`/api/market/documents/search?keyword=${encodeURIComponent(keyword)}`),
};

// Datasets API (Data Market)
export const datasetsApi = {
  list: (params?: { dataset_type?: string; category?: string; tags?: string; is_public?: boolean; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.dataset_type) searchParams.set('dataset_type', params.dataset_type);
    if (params?.category) searchParams.set('category', params.category);
    if (params?.tags) searchParams.set('tags', params.tags);
    if (params?.is_public !== undefined) searchParams.set('is_public', String(params.is_public));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    const query = searchParams.toString();
    return request<import('@/types').Dataset[]>(`/api/market/datasets${query ? `?${query}` : ''}`);
  },

  get: (id: string) => request<import('@/types').Dataset>(`/api/market/datasets/${id}`),

  create: (data: import('@/types').CreateDatasetRequest) =>
    request<import('@/types').Dataset>('/api/market/datasets', {
      method: 'POST',
      body: data,
    }),

  upload: (file: File, data: { name: string; description?: string; category?: string; tags?: string; is_public?: boolean }) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', data.name);
    if (data.description) formData.append('description', data.description);
    if (data.category) formData.append('category', data.category);
    if (data.tags) formData.append('tags', data.tags);
    formData.append('is_public', String(data.is_public ?? false));

    return request<import('@/types').Dataset>('/api/market/datasets/upload', {
      method: 'POST',
      body: formData,
    });
  },

  update: (id: string, data: Partial<import('@/types').CreateDatasetRequest>) =>
    request<import('@/types').Dataset>(`/api/market/datasets/${id}`, {
      method: 'PUT',
      body: data,
    }),

  delete: (id: string) => request<void>(`/api/market/datasets/${id}`, {
    method: 'DELETE',
  }),

  updateVisibility: (id: string, isPublic: boolean) =>
    request<import('@/types').Dataset>(`/api/market/datasets/${id}/visibility`, {
      method: 'PATCH',
      body: { is_public: isPublic },
    }),
};

// Skills API (Skill Market)
export const skillsApi = {
  list: (params?: { category?: string; tags?: string; is_public?: boolean; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.set('category', params.category);
    if (params?.tags) searchParams.set('tags', params.tags);
    if (params?.is_public !== undefined) searchParams.set('is_public', String(params.is_public));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    const query = searchParams.toString();
    return request<import('@/types').Skill[]>(`/api/market/skills${query ? `?${query}` : ''}`);
  },

  // 列出文件系统中的公共技能（内置技能）
  listFilesystem: () => request<{ name: string; description: string; category: string; tags: string[]; allowed_tools: string[]; folder_name: string }[]>('/api/market/skills/filesystem'),

  get: (id: string) => request<import('@/types').Skill>(`/api/market/skills/${id}`),

  create: (data: import('@/types').CreateSkillRequest) =>
    request<import('@/types').Skill>('/api/market/skills', {
      method: 'POST',
      body: data,
    }),

  upload: (file: File, data: { name: string; description?: string; category?: string; tags?: string; is_public?: boolean }) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', data.name);
    if (data.description) formData.append('description', data.description);
    if (data.category) formData.append('category', data.category);
    if (data.tags) formData.append('tags', data.tags);
    formData.append('is_public', String(data.is_public ?? false));

    return request<import('@/types').Skill>('/api/market/skills/upload', {
      method: 'POST',
      body: formData,
    });
  },

  update: (id: string, data: Partial<import('@/types').CreateSkillRequest>) =>
    request<import('@/types').Skill>(`/api/market/skills/${id}`, {
      method: 'PUT',
      body: data,
    }),

  delete: (id: string) => request<void>(`/api/market/skills/${id}`, {
    method: 'DELETE',
  }),

  updateVisibility: (id: string, isPublic: boolean) =>
    request<import('@/types').Skill>(`/api/market/skills/${id}/visibility`, {
      method: 'PATCH',
      body: { is_public: isPublic },
    }),
};
