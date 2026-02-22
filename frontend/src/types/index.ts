// API Types
export interface LLMProvider {
  id: string;
  user_id: string;
  name: string;
  provider_type: string;
  api_base: string;
  api_key: string;
  default_model?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Agent {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  provider_id?: string;
  model: string;
  max_steps: number;
  workspace_dir?: string;
  created_at: string;
  updated_at?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatSession {
  id: string;
  agent_id: string;
  title?: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at?: string;
}

export interface CreateProviderRequest {
  name: string;
  provider_type: string;
  api_base: string;
  api_key: string;
  default_model?: string;
  is_active?: boolean;
}

export interface CreateAgentRequest {
  name: string;
  description?: string;
  system_prompt?: string;
  provider_id?: string;
  model: string;
  max_steps?: number;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}
