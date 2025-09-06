// Knowledge components exports
export { KnowledgeSourceSelector } from './KnowledgeSourceSelector';
export { FileUploadSource } from './sources/FileUploadSource';
export { UrlInputSource } from './sources/UrlInputSource';
export { AudioUploadSource } from './sources/AudioUploadSource';

// Re-export types for convenience
export type {
  SourceType,
  KnowledgeNodeInfo,
  SourceUploadResult,
  SourceComponentProps,
  ExtendedNodeData
} from '../../types/knowledge';