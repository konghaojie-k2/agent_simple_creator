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
export type ExperimentType = 'skill_creation' | 'document' | 'document_generation' | 'problem_solving' | 'data_analysis' | 'collaboration' | 'custom';
export type ExperimentStatus = 'pending' | 'running' | 'success' | 'failed';

export type CollaborationType = 'sequential' | 'parallel' | 'debate';
export type ParticipantRole = 'leader' | 'worker' | 'reviewer' | 'observer';
export type ParticipantStatus = 'pending' | 'active' | 'completed' | 'failed';

export interface ExperimentParticipant {
  id: string;
  experiment_id: string;
  user_id: string;
  agent_id: string;
  role: ParticipantRole;
  join_order: number;
  status: ParticipantStatus;
  config: Record<string, unknown>;
  created_at: string;
  updated_at?: string;
}

export interface CollaborationConfig {
  collaboration_type: CollaborationType;
  participants: ExperimentParticipantCreate[];
  workflow_config: Record<string, unknown>;
  shared_materials: Record<string, unknown>[];
}

export interface ExperimentParticipantCreate {
  agent_id: string;
  role: ParticipantRole;
  join_order: number;
  config?: Record<string, unknown>;
}

export interface AgentMessage {
  timestamp: string;
  from: string;
  to: string;
  message: {
    step?: string;
    output?: Record<string, unknown>;
    round?: number;
    action?: string;
  };
}

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
  collaboration_type?: CollaborationType;
  workflow_config: Record<string, unknown>;
  participants: ExperimentParticipant[];
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
  collaboration_type?: CollaborationType;
  workflow_config?: Record<string, unknown>;
}

export interface CreateCollaborationExperimentRequest {
  name: string;
  description?: string;
  experiment_type: ExperimentType;
  template_id?: string;
  input_data?: Record<string, unknown>;
  collaboration_type: CollaborationType;
  participants: ExperimentParticipantCreate[];
  workflow_config?: Record<string, unknown>;
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

// Agent Detail Types
export interface ToolInfo {
  name: string;
  description: string;
}

export interface SkillInfo {
  name: string;
  description: string;
  source: 'shared' | 'agent' | 'experience';
}

export interface AgentDirectoryInfo {
  agent_dir: string;
  skills_dir: string;
  experiences_dir: string;
  workspace_dir?: string;  // Agent无独立工作空间，工作空间在实验中
}

export interface AgentDetail extends Agent {
  tools: ToolInfo[];
  skills: SkillInfo[];
  directories: AgentDirectoryInfo;
}

// Cross-Agent Experience Types
export type ExperienceStatus = 'verified' | 'draft' | 'deprecated';

export interface UserExperience {
  id: string;
  user_id: string;
  source_agent_id: string;
  source_experiment_id?: string;
  type: string;
  situation: string;
  action: string;
  result: string;
  lesson: string;
  solution: string;
  skills_used: string[];
  skills_discovered: string[];
  status: ExperienceStatus;
  applied_count: number;
  success_count: number;
  last_applied_at?: string;
  created_at: string;
}
