import { apiFetch } from './api';
import {
  KnowledgeNodeInfo,
  SupportedTypesResponse,
  SourceUploadResult,
  FileSourceInput,
  UrlSourceInput,
  AudioSourceInput
} from '../types/knowledge';

export class KnowledgeApi {
  /**
   * Upload a file to a knowledge node
   */
  static async uploadFile(
    agentId: string,
    nodeId: string,
    input: FileSourceInput
  ): Promise<SourceUploadResult> {
    const formData = new FormData();
    formData.append('file', input.file);
    
    if (input.description) {
      formData.append('description', input.description);
    }

    return apiFetch(`/knowledge/upload/${agentId}/${nodeId}`, {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * Add a URL as a knowledge source
   */
  static async uploadUrl(
    agentId: string,
    nodeId: string,
    input: UrlSourceInput
  ): Promise<SourceUploadResult> {
    return apiFetch(`/knowledge/url/${agentId}/${nodeId}`, {
      method: 'POST',
      body: JSON.stringify({
        url: input.url,
        description: input.description
      }),
    });
  }

  /**
   * Upload an audio file for transcription
   */
  static async uploadAudio(
    agentId: string,
    nodeId: string,
    input: AudioSourceInput
  ): Promise<SourceUploadResult> {
    const formData = new FormData();
    formData.append('file', input.file);
    
    if (input.description) {
      formData.append('description', input.description);
    }

    return apiFetch(`/knowledge/audio/${agentId}/${nodeId}`, {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * Get information about a knowledge node
   */
  static async getKnowledgeInfo(
    agentId: string,
    nodeId: string
  ): Promise<KnowledgeNodeInfo | null> {
    try {
      return await apiFetch(`/knowledge/info/${agentId}/${nodeId}`);
    } catch (error) {
      // Return null if not found instead of throwing
      if (error instanceof Error && error.message.includes('404')) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Get supported source types
   */
  static async getSupportedTypes(): Promise<SupportedTypesResponse> {
    return apiFetch('/knowledge/supported-types');
  }

  /**
   * Validate file before upload
   */
  static validateFile(file: File, maxSize: number = 25 * 1024 * 1024): { isValid: boolean; error?: string } {
    if (!file) {
      return { isValid: false, error: 'No file selected' };
    }

    if (file.size > maxSize) {
      return { 
        isValid: false, 
        error: `File too large. Maximum size is ${Math.round(maxSize / 1024 / 1024)}MB` 
      };
    }

    if (file.size === 0) {
      return { isValid: false, error: 'File is empty' };
    }

    return { isValid: true };
  }

  /**
   * Validate URL before upload
   */
  static validateUrl(url: string): { isValid: boolean; error?: string } {
    if (!url || !url.trim()) {
      return { isValid: false, error: 'URL is required' };
    }

    try {
      const urlObj = new URL(url);
      if (!['http:', 'https:'].includes(urlObj.protocol)) {
        return { isValid: false, error: 'Only HTTP and HTTPS URLs are supported' };
      }
      return { isValid: true };
    } catch {
      return { isValid: false, error: 'Invalid URL format' };
    }
  }

  /**
   * Get supported file extensions for file upload
   */
  static getSupportedFileExtensions(): string[] {
    return [
      '.txt', '.pdf', '.docx', '.doc', // Documents
      '.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus' // Audio
    ];
  }

  /**
   * Get MIME types for audio files
   */
  static getAudioMimeTypes(): string[] {
    return [
      'audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/flac', 
      'audio/ogg', 'audio/opus', 'audio/x-wav', 'audio/wave'
    ];
  }

  /**
   * Get MIME types for document files
   */
  static getDocumentMimeTypes(): string[] {
    return [
      'text/plain',
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword'
    ];
  }

  /**
   * Determine source type from file
   */
  static getSourceTypeFromFile(file: File): 'file' | 'audio' | null {
    const audioTypes = this.getAudioMimeTypes();
    const documentTypes = this.getDocumentMimeTypes();

    if (audioTypes.includes(file.type)) {
      return 'audio';
    }
    
    if (documentTypes.includes(file.type)) {
      return 'file';
    }

    // Fallback to extension check
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    const audioExtensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus'];
    const documentExtensions = ['.txt', '.pdf', '.docx', '.doc'];

    if (audioExtensions.includes(extension)) {
      return 'audio';
    }
    
    if (documentExtensions.includes(extension)) {
      return 'file';
    }

    return null;
  }
}