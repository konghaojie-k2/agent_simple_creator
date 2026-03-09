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

// Agent Types
export interface AgentPromptConfig {
  inject_experiences: boolean;
  max_experiences: number;
  injection_mode: string;
}

export interface AgentIdentity {
  name?: string;
  creature?: string;
  vibe?: string;
  emoji?: string;
  avatar?: string;
}

export interface AgentCapabilities {
  core_capabilities: string[];
  learned_skills: string[];
  successful_patterns: string[];
  problem_domains?: string[];
  statistics?: {
    total_experiences: number;
    success_count: number;
    failure_count: number;
  };
}

export interface Agent {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  identity?: AgentIdentity;
  capabilities?: AgentCapabilities;
  prompt_config?: AgentPromptConfig;
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
  identity?: AgentIdentity;
  capabilities?: AgentCapabilities;
  prompt_config?: AgentPromptConfig;
  provider_id?: string;
  model: string;
  max_steps?: number;
}

// User Soul Types
export interface UserSoul {
  user_id: string;
  core_truths?: string[];
  boundaries?: string[];
  vibe?: string;
  soul_content?: string;
  created_at?: string;
  updated_at?: string;
}

export interface SoulUpdateRequest {
  core_truths?: string[];
  boundaries?: string[];
  vibe?: string;
  soul_content?: string;
}

export interface PromptPreviewRequest {
  task_description: string;
}

export interface PromptPreviewResponse {
  agent_id: string;
  task_description: string;
  dynamic_prompt: string;
  base_prompt?: string;
  capabilities?: AgentCapabilities;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

// Experiment Types
export type ExperimentType = 'skill_creation' | 'document' | 'document_generation' | 'problem_solving' | 'data_analysis' | 'collaboration' | 'custom';
export type ExperimentStatus = 'pending' | 'running' | 'sense' | 'plan' | 'act' | 'reflect' | 'success' | 'failed';

export type CollaborationType = 'sequential' | 'parallel' | 'debate' | 'hierarchical';
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
  // 新增：Agent 关系配置
  depends_on?: string[];
  message_to?: string;
  parent_id?: string;
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
  // 新增：Agent 关系配置
  depends_on?: string[];
  message_to?: string;
  parent_id?: string;
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
  // Background Info (Hybrid Mode)
  requirements?: string;
  background?: string;
  doc_ids: string[];
  data_ids: string[];
  skill_ids: string[];
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
  // Background Info (Hybrid Mode)
  requirements?: string;
  background?: string;
  doc_ids?: string[];
  data_ids?: string[];
  skill_ids?: string[];
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

// Document Types
export interface Document {
  id: string;
  name: string;
  description?: string;
  doc_type: string;
  content?: string;
  file_path?: string;
  tags: string[];
  category?: string;
  is_public: boolean;
  source: string;  // "database" or "filesystem"
  user_id: string;
  created_at: string;
  updated_at?: string;
}

export interface CreateDocumentRequest {
  name: string;
  description?: string;
  doc_type?: string;
  content?: string;
  file_path?: string;
  tags?: string[];
  category?: string;
  is_public?: boolean;
}

// Dataset Types
export interface Dataset {
  id: string;
  name: string;
  description?: string;
  dataset_type: string;
  schema: Record<string, unknown>;
  file_path?: string;
  row_count: number;
  tags: string[];
  category?: string;
  is_public: boolean;
  source: string;  // "database" or "filesystem"
  user_id: string;
  created_at: string;
  updated_at?: string;
}

export interface CreateDatasetRequest {
  name: string;
  description?: string;
  dataset_type?: string;
  schema?: Record<string, unknown>;
  file_path?: string;
  row_count?: number;
  tags?: string[];
  category?: string;
  is_public?: boolean;
}

// Skill Types
export interface Skill {
  id: string;
  name: string;
  description?: string;
  category: string;
  content?: string;
  content_type: string;
  parameters_schema: Record<string, unknown>;
  tags: string[];
  usage_count: number;
  is_public: boolean;
  source: string;  // "database" or "filesystem"
  user_id: string;
  created_at: string;
  updated_at?: string;
}

export interface CreateSkillRequest {
  name: string;
  description?: string;
  category?: string;
  content?: string;
  content_type?: string;
  parameters_schema?: Record<string, unknown>;
  tags?: string[];
  is_public?: boolean;
}
