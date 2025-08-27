import { Handle, Position } from "react-flow-renderer";

interface CustomNodeProps {
  data: any;
  id: string;
  selected: boolean;
  isConnectable: boolean;
  onOpenModal: (data: any) => void;
}

export const CustomNode = ({ data, onOpenModal }: CustomNodeProps) => {
  return (
    <div
      className="bg-white border p-2 rounded shadow relative cursor-pointer"
    >
      <div>{data.label}</div>

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