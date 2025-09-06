import { useState, useCallback } from 'react';
import {
  KnowledgeNodeInfo,
  SupportedTypesResponse,
  SourceUploadResult,
  FileSourceInput,
  UrlSourceInput,
  AudioSourceInput,
  UseKnowledgeSourceReturn
} from '../types/knowledge';
import { KnowledgeApi } from '../lib/knowledgeApi';

export const useKnowledgeSource = (): UseKnowledgeSourceReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadFile = useCallback(async (
    agentId: string,
    nodeId: string,
    input: FileSourceInput
  ): Promise<SourceUploadResult> => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await KnowledgeApi.uploadFile(agentId, nodeId, input);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const uploadUrl = useCallback(async (
    agentId: string,
    nodeId: string,
    input: UrlSourceInput
  ): Promise<SourceUploadResult> => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await KnowledgeApi.uploadUrl(agentId, nodeId, input);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const uploadAudio = useCallback(async (
    agentId: string,
    nodeId: string,
    input: AudioSourceInput
  ): Promise<SourceUploadResult> => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await KnowledgeApi.uploadAudio(agentId, nodeId, input);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getKnowledgeInfo = useCallback(async (
    agentId: string,
    nodeId: string
  ): Promise<KnowledgeNodeInfo | null> => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await KnowledgeApi.getKnowledgeInfo(agentId, nodeId);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get knowledge info';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getSupportedTypes = useCallback(async (): Promise<SupportedTypesResponse> => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await KnowledgeApi.getSupportedTypes();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get supported types';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    uploadFile,
    uploadUrl,
    uploadAudio,
    getKnowledgeInfo,
    getSupportedTypes,
    isLoading,
    error
  };
};