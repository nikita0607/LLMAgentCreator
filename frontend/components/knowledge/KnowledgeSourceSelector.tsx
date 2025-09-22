import React, { useState, useEffect } from 'react';
import * as knowledgeTypes from '../../types/knowledge';
import {
  SourceType,
  KnowledgeSourceSelectorProps,
  SourceUploadResult,
  SourceComponentProps
} from '../../types/knowledge';
import { KnowledgeApi } from '../../lib/knowledgeApi';
import { FileUploadSource } from './sources/FileUploadSource';
import { UrlInputSource } from './sources/UrlInputSource';
import { AudioUploadSource } from './sources/AudioUploadSource';
import { ErrorBoundary } from '../ErrorBoundary';
import { LoadingSpinner } from '../LoadingSpinner';

interface KnowledgeSourceSelectorState {
  selectedType: SourceType | null;
  supportedTypes: Record<string, string[]> | null;
  isLoading: boolean;
  error: string | null;
}

interface ExtendedKnowledgeSourceSelectorProps {
  agentId: string;
  nodeId: string;
  onUploadSuccess: (result: SourceUploadResult) => void;
  onError: (error: string) => void;
  onSourceSelected?: (sourceType: SourceType) => void;
  selectedType?: SourceType;
  supportedTypes?: knowledgeTypes.SupportedTypesResponse;
}

// Source type configurations
type FileSourceConfig = {
  type: SourceType;
  label: string;
  icon: string;
  description: string;
  acceptedFileTypes: string[];
  component: React.ComponentType<any>;
};

type WebSourceConfig = {
  type: SourceType;
  label: string;
  icon: string;
  description: string;
  component: React.ComponentType<any>;
};

type AudioSourceConfig = {
  type: SourceType;
  label: string;
  icon: string;
  description: string;
  acceptedFileTypes: string[];
  component: React.ComponentType<any>;
};

type SourceConfig = FileSourceConfig | WebSourceConfig | AudioSourceConfig;

const SOURCE_TYPE_CONFIGS: Record<string, SourceConfig> = {
  file: {
    type: 'file' as SourceType,
    label: 'Document',
    icon: '📄',
    description: 'Upload text documents (PDF, DOCX, TXT)',
    acceptedFileTypes: ['.txt', '.pdf', '.docx', '.doc'],
    component: FileUploadSource
  },
  web: {
    type: 'web' as SourceType,
    label: 'Web Page',
    icon: '🌐',
    description: 'Extract content from web pages',
    component: UrlInputSource
  },
  audio: {
    type: 'audio' as SourceType,
    label: 'Audio',
    icon: '🎵',
    description: 'Transcribe audio files to text',
    acceptedFileTypes: ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus'],
    component: AudioUploadSource
  }
};

export const KnowledgeSourceSelector: React.FC<ExtendedKnowledgeSourceSelectorProps> = ({
  agentId,
  nodeId,
  onUploadSuccess,
  onError,
  selectedType: initialSelectedType,
  supportedTypes: initialSupportedTypes
}) => {
  const [state, setState] = useState<KnowledgeSourceSelectorState>({
    selectedType: initialSelectedType || null,
    supportedTypes: initialSupportedTypes?.supported_types || null,
    isLoading: false,
    error: null
  });

  // Load supported types on mount if not provided
  useEffect(() => {
    if (!state.supportedTypes) {
      loadSupportedTypes();
    }
  }, []);

  const loadSupportedTypes = async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const supportedTypes = await KnowledgeApi.getSupportedTypes();
      setState(prev => ({
        ...prev,
        supportedTypes: supportedTypes.supported_types,
        isLoading: false
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load supported types';
      setState(prev => ({
        ...prev,
        error: errorMessage,
        isLoading: false
      }));
      onError(errorMessage);
    }
  };

  const handleTypeSelect = (type: SourceType) => {
    setState(prev => ({ ...prev, selectedType: type, error: null }));
  };

  const handleUploadSuccess = (result: SourceUploadResult) => {
    onUploadSuccess(result);
    // Reset selection to allow for another upload
    setState(prev => ({ ...prev, selectedType: null }));
  };

  const handleUploadError = (error: string) => {
    setState(prev => ({ ...prev, error }));
    onError(error);
  };

  const renderSourceTypeButton = (config: typeof SOURCE_TYPE_CONFIGS[keyof typeof SOURCE_TYPE_CONFIGS]) => {
    const isSelected = state.selectedType === config.type;
    const isAvailable = state.supportedTypes && 
      Object.values(state.supportedTypes).some(types => 
        types.some(type => 
          type.toLowerCase().includes(config.type) || 
          config.type === 'file' && ['text', 'pdf', 'docx'].some(t => type.toLowerCase().includes(t)) ||
          config.type === 'web' && ['web', 'url', 'html'].some(t => type.toLowerCase().includes(t)) ||
          config.type === 'audio' && ['audio', 'speech', 'transcription'].some(t => type.toLowerCase().includes(t))
        )
      );

    return (
      <button
        key={config.type}
        onClick={() => handleTypeSelect(config.type)}
        disabled={!isAvailable || state.isLoading}
        className={`p-4 border-2 rounded-lg text-left transition-all ${
          isSelected
            ? 'border-blue-500 bg-blue-50'
            : isAvailable
            ? 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            : 'border-gray-100 bg-gray-50 cursor-not-allowed opacity-50'
        }`}
      >
        <div className="flex items-start space-x-3">
          <div className="text-2xl">{config.icon}</div>
          <div className="flex-1">
            <div className="font-medium text-gray-900">{config.label}</div>
            <div className="text-sm text-gray-500 mt-1">{config.description}</div>
            {!isAvailable && (
              <div className="text-xs text-red-500 mt-1">Not available</div>
            )}
          </div>
        </div>
      </button>
    );
  };

  const renderSelectedSourceComponent = () => {
    if (!state.selectedType) return null;

    const config = SOURCE_TYPE_CONFIGS[state.selectedType];
    if (!config) return null;

    const SourceComponent = config.component;
    const commonProps: SourceComponentProps = {
      onUpload: handleUploadSuccess,
      onError: handleUploadError,
      isLoading: state.isLoading,
      disabled: false
    };

    // Type guard to check if config has acceptedFileTypes
    const hasAcceptedFileTypes = (config: SourceConfig): config is FileSourceConfig | AudioSourceConfig => {
      return 'acceptedFileTypes' in config;
    };

    return (
      <div className="mt-6 p-4 border border-gray-200 rounded-lg bg-gray-50">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            {config.icon} {config.label}
          </h3>
          <button
            onClick={() => setState(prev => ({ ...prev, selectedType: null }))}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
        
        <SourceComponent
          {...commonProps}
          agentId={agentId}
          nodeId={nodeId}
          {...(hasAcceptedFileTypes(config) && config.acceptedFileTypes ? { acceptedFileTypes: config.acceptedFileTypes } : {})}
        />

      </div>
    );
  };

  if (state.isLoading && !state.supportedTypes) {
    return (
      <LoadingSpinner 
        size="md" 
        text="Loading source types..."
        className="p-8"
      />
    );
  }

  return (
    <ErrorBoundary>
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Choose Knowledge Source
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Select the type of content you want to add to this knowledge node.
          </p>
        </div>

        {/* Error Display */}
        {state.error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <div className="flex items-start space-x-2">
              <span className="text-red-500 text-sm">⚠️</span>
              <div>
                <div className="text-sm text-red-800 font-medium">Error</div>
                <div className="text-sm text-red-700">{state.error}</div>
              </div>
            </div>
          </div>
        )}

        {/* Source Type Selection */}
        {!state.selectedType && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.values(SOURCE_TYPE_CONFIGS).map(config => renderSourceTypeButton(config))}
          </div>
        )}

        {/* Selected Source Component */}
        {renderSelectedSourceComponent()}

        {/* Help Text */}
        {!state.selectedType && (
          <div className="text-xs text-gray-500 mt-4">
            💡 Tip: Each source type will be processed differently to extract the most relevant text content.
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
};