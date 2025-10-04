import { Handle, Position } from "react-flow-renderer";
import { ExtendedNodeData } from "../../../types/knowledge";

interface CustomNodeProps {
  data: ExtendedNodeData;
  id: string;
  selected: boolean;
  isConnectable: boolean;
  isStartNode?: boolean; // Add prop to indicate if this is the start node
}

interface ForcedMessageNodeData extends ExtendedNodeData {
  forced_text?: string;
  reference_node_id?: string;
}

interface LLMRequestNodeData extends ExtendedNodeData {
  system_prompt?: string;
}

export const CustomNode = ({ data, id, isStartNode = false }: CustomNodeProps) => {
  // Helper function to get node type display name
  const getNodeTypeDisplayName = (nodeType: string) => {
    switch (nodeType) {
      case 'knowledge': return 'RAG Module';
      case 'conditional_llm': return 'LLM Module';
      case 'webhook': return 'Webhook';
      case 'forced_message': return 'Forced Message';
      case 'wait_for_user_input': return 'Wait for Input';
      case 'llm_request': return 'LLM Request';
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
      className={`${
        isStartNode 
          ? 'bg-gray-800 border-green-400 border-2 shadow-lg shadow-green-400/20' 
          : 'bg-gray-900 border border-gray-600'
      } p-3 font-mono relative min-w-[160px] hover:border-green-400 transition-all duration-200`}
      style={{ 
        minHeight: getNodeHeight(),
        borderRadius: '0.25rem',
        boxShadow: isStartNode 
          ? '0 0 20px rgba(126, 231, 135, 0.3)' 
          : '0 2px 8px rgba(0, 0, 0, 0.3)'
      }}
    >
      {/* Terminal-style start node indicator */}
      {isStartNode && (
        <div 
          className="absolute -top-2 -left-2 bg-green-500 text-black text-xs px-2 py-1 font-bold"
          style={{ borderRadius: '0.25rem' }}
        >
          MAIN
        </div>
      )}
      
      <div className={`text-xs font-bold uppercase tracking-wide mb-2 ${
        isStartNode ? 'text-green-400' : 'text-cyan-400'
      }`}>
        [{getNodeTypeDisplayName(data.type)}]
      </div>
      <div className={`font-medium text-sm ${
        isStartNode ? 'text-green-300' : 'text-gray-200'
      }`}>
        {data.label}
      </div>
      
      {/* Terminal-style source information for knowledge nodes */}
      {data.type === "knowledge" && (
        <div className="text-xs text-gray-300 mt-2 space-y-1 border-l-2 border-gray-600 pl-2">
          <div className="flex items-center space-x-1">
            <span>{getSourceTypeIcon(data.source_type || 'file')}</span>
            <span className="text-cyan-400 font-mono">
              {getSourceDisplayName(data)}
            </span>
          </div>
          
          {/* Show last updated if available */}
          {data.updated_at && (
            <div className="text-xs text-gray-500">
              updated: {new Date(data.updated_at).toLocaleDateString()}
            </div>
          )}
          
          {/* Show source type badge */}
          {data.source_type && (
            <div className={`inline-block px-1 py-0.5 text-xs font-medium border ${
              data.source_type === 'web' ? 'bg-blue-900 text-blue-300 border-blue-500' :
              data.source_type === 'audio' ? 'bg-purple-900 text-purple-300 border-purple-500' :
              'bg-gray-900 text-gray-300 border-gray-500'
            }`}
            style={{ borderRadius: '0.25rem' }}
            >
              {data.source_type}
            </div>
          )}
        </div>
      )}

      {/* Terminal-style forced message display */}
      {data.type === "forced_message" && (
        <div className="text-xs text-gray-300 mt-2 p-2 bg-gray-800 border border-blue-500" style={{ borderRadius: '0.25rem' }}>
          <div className="font-medium text-blue-400 mb-1">auto_message:</div>
          {(data as ForcedMessageNodeData).reference_node_id ? (
            <div className="text-gray-300 font-mono break-words">
              "Referencing node: {(data as ForcedMessageNodeData).reference_node_id}"
            </div>
          ) : (data as ForcedMessageNodeData).forced_text ? (
            <div className="text-gray-300 font-mono break-words">
              "{(data as ForcedMessageNodeData).forced_text!.length > 40 
                ? `${(data as ForcedMessageNodeData).forced_text!.substring(0, 40)}...` 
                : (data as ForcedMessageNodeData).forced_text}"
            </div>
          ) : (
            <div className="text-gray-500 italic">No message configured</div>
          )}
        </div>
      )}

      {/* Terminal-style conditional branches display */}
      {data.type === "conditional_llm" && data.branches && data.branches.length > 0 && (
        <div className="text-xs text-gray-300 mt-2 space-y-1">
          <div className="font-medium text-purple-400">branches:</div>
          {data.branches.map((branch, index) => (
            <div 
              key={branch.id} 
              className="text-xs bg-gray-800 px-2 py-1 border-l-2 flex items-center justify-between font-mono"
              style={{
                borderRadius: '0.25rem',
                borderLeftColor: `hsl(${(index * 360) / Math.max(data.branches!.length, 1)}, 70%, 50%)`
              }}
            >
              <span className="text-gray-300">
                if ({branch.condition_text.length > 20 
                  ? `${branch.condition_text.substring(0, 20)}...` 
                  : branch.condition_text})
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
            <div className="text-xs bg-gray-800 px-2 py-1 border-l-2 border-gray-500 flex items-center justify-between font-mono" style={{ borderRadius: '0.25rem' }}>
              <span className="text-gray-400">else (default)</span>
              <div className="w-2 h-2 rounded-full ml-2 flex-shrink-0 bg-gray-500" />
            </div>
          )}
        </div>
      )}

      {/* Terminal-style LLM request display */}
      {data.type === "llm_request" && (
        <div className="text-xs text-gray-300 mt-2 space-y-1 border-l-2 border-gray-600 pl-2">
          <div className="font-medium text-yellow-400">LLM Request Node</div>
          {data.system_prompt && (
            <div className="text-xs text-gray-300">
              <span className="text-cyan-400">System Prompt:</span> {data.system_prompt.length > 30 ? `${data.system_prompt.substring(0, 30)}...` : data.system_prompt}
            </div>
          )}

          <div className="text-xs text-blue-400">
            Uses connected knowledge & webhook context
          </div>
        </div>
      )}

      {/* Terminal-style input handle */}
      <Handle
        type="target"
        position={Position.Left}
        id="input"
        style={{ 
          top: '50%', 
          transform: 'translateY(-50%)', 
          background: '#4ec9b0',
          border: '2px solid #0d1117',
          width: '12px',
          height: '12px'
        }}
      />

      {/* Terminal-style output handles */}
      {data.type === "webhook" ? (
        <>
          <Handle 
            type="source" 
            position={Position.Right} 
            id="success" 
            style={{ 
              top: '30%', 
              background: '#7ee787',
              border: '2px solid #0d1117',
              width: '12px',
              height: '12px'
            }} 
          />
          <Handle 
            type="source" 
            position={Position.Right} 
            id="failure" 
            style={{ 
              top: '70%', 
              background: '#f85149',
              border: '2px solid #0d1117',
              width: '12px',
              height: '12px'
            }} 
          />
        </>
      ) : data.type === "conditional_llm" ? (
        <>
          {data.branches && data.branches.map((branch, index) => {
            // Calculate position to align with each branch preview item
            const titleHeight = 50;
            const branchesHeaderHeight = 18;
            const baseOffset = titleHeight + branchesHeaderHeight;
            const branchItemHeight = 30;
            const branchCenterOffset = 16;
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
                  border: '2px solid #0d1117',
                  position: 'absolute',
                  right: '-8px',
                  width: '12px',
                  height: '12px'
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
                top: `${50 + 18 + ((data.branches?.length || 0) * 30) + 16}px`,
                background: '#7d8590',
                border: '2px solid #0d1117',
                position: 'absolute',
                right: '-8px',
                width: '12px',
                height: '12px'
              }}
            />
          )}
        </>
      ) : (
        <Handle 
          type="source" 
          position={Position.Right} 
          id="default" 
          style={{ 
            top: '50%', 
            background: '#4ec9b0',
            border: '2px solid #0d1117',
            width: '12px',
            height: '12px'
          }} 
        />
      )}
    </div>
  );
};