import React, { useState } from 'react';
import { SourceComponentProps, UrlSourceInput } from '../../../types/knowledge';
import { KnowledgeApi } from '../../../lib/knowledgeApi';

interface UrlInputSourceProps extends SourceComponentProps {
  agentId: string;
  nodeId: string;
}

export const UrlInputSource: React.FC<UrlInputSourceProps> = ({
  agentId,
  nodeId,
  onUpload,
  onError,
  isLoading = false,
  disabled = false
}) => {
  const [url, setUrl] = useState('');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url.trim()) {
      onError('Please enter a URL');
      return;
    }

    const validation = KnowledgeApi.validateUrl(url.trim());
    if (!validation.isValid) {
      onError(validation.error || 'Invalid URL');
      return;
    }

    setUploading(true);
    try {
      const input: UrlSourceInput = {
        url: url.trim(),
        description: description.trim() || undefined
      };

      const result = await KnowledgeApi.uploadUrl(agentId, nodeId, input);
      onUpload(result);
      
      // Reset form
      setUrl('');
      setDescription('');
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Failed to add URL');
    } finally {
      setUploading(false);
    }
  };

  const isValidUrl = (urlString: string) => {
    try {
      const urlObj = new URL(urlString);
      return ['http:', 'https:'].includes(urlObj.protocol);
    } catch {
      return false;
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="text-sm font-medium text-gray-700">
        🌐 Web Page URL
      </div>
      
      {/* URL Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Website URL *
        </label>
        <div className="relative">
          <input
            type="url"
            value={url}
            onChange={handleUrlChange}
            placeholder="https://example.com/article"
            className={`w-full p-3 pr-10 border rounded-md text-sm ${
              url && !isValidUrl(url)
                ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }`}
            disabled={disabled}
            required
          />
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            {url && isValidUrl(url) ? (
              <span className="text-green-500">✓</span>
            ) : url ? (
              <span className="text-red-500">✗</span>
            ) : null}
          </div>
        </div>
        {url && !isValidUrl(url) && (
          <p className="mt-1 text-sm text-red-600">
            Please enter a valid HTTP or HTTPS URL
          </p>
        )}
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description (optional)
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe this web page..."
          className="w-full p-2 border border-gray-300 rounded-md text-sm resize-none"
          rows={2}
          disabled={disabled}
        />
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
        <div className="text-sm text-blue-800">
          <div className="font-medium mb-1">💡 How it works:</div>
          <ul className="text-xs space-y-1 list-disc list-inside">
            <li>We'll extract the main content from the web page</li>
            <li>Navigation menus and ads are automatically filtered out</li>
            <li>Only HTTP and HTTPS URLs are supported</li>
            <li>Large pages may take a moment to process</li>
          </ul>
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={!url || !isValidUrl(url) || uploading || isLoading || disabled}
        className={`w-full py-2 px-4 rounded-md text-white font-medium ${
          !url || !isValidUrl(url) || uploading || isLoading || disabled
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700'
        }`}
      >
        {uploading ? 'Processing URL...' : 'Add Web Page'}
      </button>
    </form>
  );
};