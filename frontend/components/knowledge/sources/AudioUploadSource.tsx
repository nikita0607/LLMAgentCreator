import React, { useState, useRef } from 'react';
import { SourceComponentProps, AudioSourceInput } from '../../../types/knowledge';
import { KnowledgeApi } from '../../../lib/knowledgeApi';

interface AudioUploadSourceProps extends SourceComponentProps {
  agentId: string;
  nodeId: string;
}

export const AudioUploadSource: React.FC<AudioUploadSourceProps> = ({
  agentId,
  nodeId,
  onUpload,
  onError,
  isLoading = false,
  disabled = false
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const audioMimeTypes = KnowledgeApi.getAudioMimeTypes();
  const supportedAudioExtensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus'];

  const handleFileSelect = (file: File) => {
    const validation = KnowledgeApi.validateFile(file);
    if (!validation.isValid) {
      onError(validation.error || 'Invalid file');
      return;
    }

    // Check if file type is supported for audio
    const sourceType = KnowledgeApi.getSourceTypeFromFile(file);
    if (sourceType !== 'audio') {
      onError('This file type is not supported for audio upload. Please select an audio file.');
      return;
    }

    setSelectedFile(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      onError('Please select an audio file first');
      return;
    }

    setUploading(true);
    try {
      const input: AudioSourceInput = {
        file: selectedFile,
        description: description.trim() || undefined
      };

      const result = await KnowledgeApi.uploadAudio(agentId, nodeId, input);
      onUpload(result);
      
      // Reset form
      setSelectedFile(null);
      setDescription('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-4">
      <div className="text-sm font-medium text-gray-700">
        🎵 Audio Transcription
      </div>
      
      {/* File Drop Zone */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-6 transition-colors ${
          dragActive
            ? 'border-purple-400 bg-purple-50'
            : selectedFile
            ? 'border-green-400 bg-green-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept={audioMimeTypes.join(',')}
          onChange={handleFileInputChange}
          disabled={disabled}
        />
        
        <div className="text-center">
          {selectedFile ? (
            <div className="space-y-2">
              <div className="text-green-600">
                ✅ {selectedFile.name}
              </div>
              <div className="text-sm text-gray-500">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemoveFile();
                }}
                className="text-red-600 hover:text-red-800 text-sm"
                disabled={disabled}
              >
                Remove file
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="text-gray-400 text-2xl">🎵</div>
              <div className="text-gray-600">
                Click to browse or drag and drop audio file
              </div>
              <div className="text-sm text-gray-500">
                Supported: {supportedAudioExtensions.join(', ')}
              </div>
              <div className="text-xs text-gray-400">
                Maximum file size: 25MB
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description (optional)
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe this audio content..."
          className="w-full p-2 border border-gray-300 rounded-md text-sm resize-none"
          rows={2}
          disabled={disabled}
        />
      </div>

      {/* Info Box */}
      <div className="bg-purple-50 border border-purple-200 rounded-md p-3">
        <div className="text-sm text-purple-800">
          <div className="font-medium mb-1">🎙️ Transcription Info:</div>
          <ul className="text-xs space-y-1 list-disc list-inside">
            <li>Audio will be automatically transcribed to text</li>
            <li>Supports multiple languages and accents</li>
            <li>Processing time depends on audio length</li>
            <li>Text accuracy may vary based on audio quality</li>
          </ul>
        </div>
      </div>

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={!selectedFile || uploading || isLoading || disabled}
        className={`w-full py-2 px-4 rounded-md text-white font-medium ${
          !selectedFile || uploading || isLoading || disabled
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-purple-600 hover:bg-purple-700'
        }`}
      >
        {uploading ? 'Transcribing Audio...' : 'Upload & Transcribe'}
      </button>
    </div>
  );
};