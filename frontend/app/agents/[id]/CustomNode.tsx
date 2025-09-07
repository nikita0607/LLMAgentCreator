import { Handle, Position } from "react-flow-renderer";
import { ExtendedNodeData } from "../../../types/knowledge";

interface CustomNodeProps {
  data: ExtendedNodeData;
  id: string;
  selected: boolean;
  isConnectable: boolean;
  isStartNode?: boolean; // Add prop to indicate if this is the start node
}

export const CustomNode = ({ data, id, isStartNode = false }: CustomNodeProps) => {
  // Helper function to get node type display name
  const getNodeTypeDisplayName = (nodeType: string) => {
    switch (nodeType) {
      case 'knowledge': return 'RAG Module';
      case 'conditional_llm': return 'LLM Module';
      case 'webhook': return 'Webhook';
      default: return nodeType;
    }
  };

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

  // Calculate dynamic height for conditional LLM nodes
  const getNodeHeight = () => {
    if (data.type === "conditional_llm" && data.branches && data.branches.length > 0) {
      const baseHeight = 60; // Base height for title and content
      const branchesHeight = data.branches.length * 28; // Each branch takes ~28px
      const defaultBranchHeight = data.default_branch ? 28 : 0;
      const paddingHeight = 10; // Minimal padding
      return baseHeight + branchesHeight + defaultBranchHeight + paddingHeight;
    }
    return undefined; // Let CSS handle height for other node types
  };

  return (
    <div
      className={`${isStartNode 
        ? 'bg-green-50 border-green-500 border-2 shadow-lg' 
        : 'bg-white border'} p-2 rounded shadow relative min-w-[150px]`}
      style={{ minHeight: getNodeHeight() }}
    >
      {/* Start node indicator */}
      {isStartNode && (
        <div className="absolute -top-2 -left-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full font-bold">
          START
        </div>
      )}
      
      <div className={`text-xs font-bold uppercase tracking-wide mb-1 ${
        isStartNode ? 'text-green-700' : 'text-blue-600'
      }`}>
        {getNodeTypeDisplayName(data.type)}
      </div>
      <div className="font-medium text-black">{data.label}</div>
      
      {/* Display source information for knowledge nodes */}
      {data.type === "knowledge" && (
        <div className="text-xs text-black mt-1 space-y-1">
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

      {/* Display conditional branches for conditional_llm nodes */}
      {data.type === "conditional_llm" && data.branches && data.branches.length > 0 && (
        <div className="text-xs text-black mt-1 space-y-1">
          <div className="font-medium text-purple-600">Conditional Branches:</div>
          {data.branches.map((branch, index) => (
            <div 
              key={branch.id} 
              className="text-xs bg-purple-50 px-2 py-1 rounded border-l-2 border-purple-300 flex items-center justify-between"
              style={{
                borderLeftColor: `hsl(${(index * 360) / Math.max(data.branches!.length, 1)}, 70%, 50%)`
              }}
            >
              <span>
                {branch.condition_text.length > 25 
                  ? `${branch.condition_text.substring(0, 25)}...` 
                  : branch.condition_text}
              </span>
              <div 
                className="w-2 h-2 rounded-full ml-2 flex-shrink-0"
                style={{
                  backgroundColor: `hsl(${(index * 360) / Math.max(data.branches!.length, 1)}, 70%, 50%)`
                }}
              />
            </div>
          ))}
          {data.default_branch && (
            <div className="text-xs bg-gray-50 px-2 py-1 rounded border-l-2 border-gray-300 flex items-center justify-between">
              <span>Default branch</span>
              <div className="w-2 h-2 rounded-full ml-2 flex-shrink-0 bg-gray-400" />
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
      ) : data.type === "conditional_llm" && data.branches ? (
        <>
          {data.branches.map((branch, index) => {
            // Calculate position to align with each branch preview item
            // Base offset accounts for the node title, "Conditional Branches:" title, and spacing
            const titleHeight = 50; // Node title height + margin
            const branchesHeaderHeight = 18; // "Conditional Branches:" header height
            const baseOffset = titleHeight + branchesHeaderHeight;
            const branchItemHeight = 30; // Height of each branch preview item including margins
            const branchCenterOffset = 16; // Center of each branch item
            const topPosition = baseOffset + (index * branchItemHeight) + branchCenterOffset;
            
            return (
              <Handle 
                key={branch.id}
                type="source" 
                position={Position.Right} 
                id={branch.id}
                style={{ 
                  top: `${topPosition}px`, 
                  background: `hsl(${(index * 360) / Math.max(data.branches!.length, 1)}, 70%, 50%)`,
                  position: 'absolute',
                  right: '-8px'
                }}
              />
            );
          })}
          {data.default_branch && (
            <Handle 
              type="source" 
              position={Position.Right} 
              id="default"
              style={{ 
                top: `${50 + 18 + (data.branches!.length * 30) + 16}px`, // titleHeight + branchesHeaderHeight + branches + centerOffset
                background: '#888',
                position: 'absolute',
                right: '-8px'
              }}
            />
          )}
        </>
      ) : (
        <Handle type="source" position={Position.Right} id="default" style={{ top: '50%', background: '#555' }} />
      )}
    </div>
  );
};