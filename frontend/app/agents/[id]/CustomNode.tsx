import { Handle, Position } from "react-flow-renderer";
import { ExtendedNodeData } from "../../../types/knowledge";

interface CustomNodeProps {
  data: ExtendedNodeData;
  id: string;
  selected: boolean;
  isConnectable: boolean;
  onOpenModal: (data: any) => void;
}

export const CustomNode = ({ data, onOpenModal }: CustomNodeProps) => {
  // Helper function to get source type icon
  const getSourceTypeIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'file': return '📄';
      case 'web': return '🌐';
      case 'audio': return '🎵';
      default: return '📄';
    }
  };

  // Helper function to format source name
  const getSourceDisplayName = (data: ExtendedNodeData) => {
    if (data.source_name) {
      // For URLs, show domain name
      if (data.source_type === 'web') {
        try {
          const url = new URL(data.source_name);
          return url.hostname;
        } catch {
          return data.source_name;
        }
      }
      // For files, show filename without extension if it's long
      if (data.source_name.length > 20) {
        const parts = data.source_name.split('.');
        const ext = parts.pop();
        const name = parts.join('.');
        return `${name.substring(0, 15)}...${ext ? '.' + ext : ''}`;
      }
      return data.source_name;
    }
    // Fallback to legacy filename property
    return data.filename || 'Unknown source';
  };

  return (
    <div
      className="bg-white border p-2 rounded shadow relative cursor-pointer min-w-[150px]"
      onClick={() => onOpenModal(data)}
    >
      <div className="font-medium">{data.label}</div>
      
      {/* Display source information for knowledge nodes */}
      {data.type === "knowledge" && (
        <div className="text-xs text-gray-500 mt-1 space-y-1">
          <div className="flex items-center space-x-1">
            <span>{getSourceTypeIcon(data.source_type || 'file')}</span>
            <span className="italic">
              {getSourceDisplayName(data)}
            </span>
          </div>
          
          {/* Show embeddings count if available */}
          {data.embeddings_count !== undefined && (
            <div className="text-xs text-blue-600">
              {data.embeddings_count} chunks
            </div>
          )}
          
          {/* Show last updated if available */}
          {data.updated_at && (
            <div className="text-xs text-gray-400">
              Updated: {new Date(data.updated_at).toLocaleDateString()}
            </div>
          )}
          
          {/* Show source type badge */}
          {data.source_type && (
            <div className={`inline-block px-1 py-0.5 rounded text-xs font-medium ${
              data.source_type === 'web' ? 'bg-blue-100 text-blue-800' :
              data.source_type === 'audio' ? 'bg-purple-100 text-purple-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {data.source_type}
            </div>
          )}
        </div>
      )}

      {/* Левый вход */}
      <Handle
        type="target"
        position={Position.Left}
        id="input"
        style={{ top: '50%', transform: 'translateY(-50%)', background: '#555' }}
      />

      {/* Правые выходы */}
      {data.type === "webhook" ? (
        <>
          <Handle type="source" position={Position.Right} id="success" style={{ top: '30%', background: 'green' }} />
          <Handle type="source" position={Position.Right} id="failure" style={{ top: '70%', background: 'red' }} />
        </>
      ) : (
        <Handle type="source" position={Position.Right} id="default" style={{ top: '50%', background: '#555' }} />
      )}
    </div>
  );
};