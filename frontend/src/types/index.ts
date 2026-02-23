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

// Experiment Types
export type ExperimentType = 'skill_creation' | 'document' | 'problem_solving' | 'data_analysis' | 'custom';
export type ExperimentStatus = 'pending' | 'running' | 'success' | 'failed';

export interface Experiment {
  id: string;
  agent_id: string;
  user_id: string;
  name: string;
  description?: string;
  experiment_type: ExperimentType;
  template_id?: string;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  status: ExperimentStatus;
  error_message?: string;
  metrics: Record<string, unknown>;
  created_at: string;
  updated_at?: string;
}

export interface CreateExperimentRequest {
  agent_id: string;
  name: string;
  description?: string;
  experiment_type: ExperimentType;
  template_id?: string;
  input_data?: Record<string, unknown>;
}

export interface UpdateExperimentRequest {
  name?: string;
  description?: string;
  input_data?: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  status?: ExperimentStatus;
  error_message?: string;
  metrics?: Record<string, unknown>;
}

export interface ExperimentRunRequest {
  input_data?: Record<string, unknown>;
}

// Experiment Template Types
export interface ExperimentTemplate {
  id: string;
  name: string;
  description?: string;
  experiment_type: ExperimentType;
  template_config: Record<string, unknown>;
  is_public: boolean;
  user_id?: string;
  created_at: string;
}

export interface CreateTemplateRequest {
  name: string;
  description?: string;
  experiment_type: ExperimentType;
  template_config?: Record<string, unknown>;
  is_public?: boolean;
}

// Experiment Experience Types
export interface ExperimentExperience {
  id: string;
  experiment_id: string;
  user_id: string;
  summary: string;
  lessons_learned?: string;
  improvements?: string;
  related_experiments: string[];
  created_at: string;
}

export interface CreateExperienceRequest {
  experiment_id: string;
  summary: string;
  lessons_learned?: string;
  improvements?: string;
  related_experiments?: string[];
}
