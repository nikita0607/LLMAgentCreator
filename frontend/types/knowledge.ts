// Types for knowledge source system

// Source type enumeration
export type SourceType = 'file' | 'web' | 'audio';

// Source input interfaces
export interface FileSourceInput {
  file: File;
  description?: string;
}

export interface UrlSourceInput {
  url: string;
  description?: string;
}

export interface AudioSourceInput {
  file: File;
  description?: string;
}

// Source upload result interface
export interface SourceUploadResult {
  status: string;
  knowledge_node_id: number;
  filename?: string;
  url?: string;
  source_type: string;
}

// Knowledge node info interface
export interface KnowledgeNodeInfo {
  id: number;
  agent_id: number;
  node_id: string;
  name: string;
  source_type: SourceType;
  source_data?: Record<string, any>;
  extractor_metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
  // Removed embeddings_count
}

// Supported types response
export interface SupportedTypesResponse {
  supported_types: Record<string, string[]>;
}

// Component props interfaces
export interface SourceComponentProps {
  onUpload: (result: SourceUploadResult) => void;
  onError: (error: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export interface KnowledgeSourceSelectorProps {
  onSourceSelected: (sourceType: SourceType) => void;
  selectedType?: SourceType;
  supportedTypes?: SupportedTypesResponse;
}

// Conditional branch interface
export interface ConditionalBranch {
  id: string;
  condition_text: string;
  next_node?: string;
}

// Extended node data interface
export interface ExtendedNodeData {
  id: string;
  label: string;
  type: "webhook" | "knowledge" | "conditional_llm" | "forced_message" | "wait_for_user_input" | "llm_request";
  action?: string;
  url?: string;
  method?: string;
  params?: NodeParam[];
  missing_param_message?: string;
  // Knowledge specific properties
  source_type?: SourceType;
  source_name?: string;
  source_metadata?: Record<string, any>;
  extractor_metadata?: Record<string, any>;
  // Removed embeddings_count
  updated_at?: string;
  // Legacy property for backward compatibility
  filename?: string;
  // Conditional LLM specific properties
  branches?: ConditionalBranch[];
  default_branch?: string;
  // Forced message specific properties
  forced_text?: string;
  reference_node_id?: string;
  // LLM Request specific properties
  system_prompt?: string;
}

export interface NodeParam {
  id: string;
  name: string;
  description: string;
  value?: string;
}

// Source type configuration
export interface SourceTypeConfig {
  type: SourceType;
  label: string;
  icon: string;
  description: string;
  acceptedFileTypes?: string[];
  component: any; // Using 'any' instead of React.ComponentType to avoid import issues
}

// API response types
export interface ApiError {
  detail: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

// Hook types
export interface UseKnowledgeSourceReturn {
  uploadFile: (agentId: string, nodeId: string, input: FileSourceInput) => Promise<SourceUploadResult>;
  uploadUrl: (agentId: string, nodeId: string, input: UrlSourceInput) => Promise<SourceUploadResult>;
  uploadAudio: (agentId: string, nodeId: string, input: AudioSourceInput) => Promise<SourceUploadResult>;
  getKnowledgeInfo: (agentId: string, nodeId: string) => Promise<KnowledgeNodeInfo | null>;
  getSupportedTypes: () => Promise<SupportedTypesResponse>;
  isLoading: boolean;
  error: string | null;
}

export interface SourceValidationResult {
  isValid: boolean;
  error?: string;
}

// Utility types
export type SourceInputUnion = FileSourceInput | UrlSourceInput | AudioSourceInput;

export interface SourceMetadata {
  [key: string]: any;
}

export interface ExtractorMetadata {
  extractor_type: string;
  processed_at: string;
  [key: string]: any;
}