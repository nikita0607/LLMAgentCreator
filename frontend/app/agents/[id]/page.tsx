"use client";

import { useEffect, useState, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  MiniMap,
  Controls,
  Background,
  Connection,
  Edge,
  Node,
  NodeChange,
  EdgeChange,
  applyNodeChanges,
  applyEdgeChanges,
} from "react-flow-renderer";
import { apiFetch } from "@/lib/api";
import { Dialog } from "@headlessui/react";
import { CustomNode } from "./CustomNode";
import { v4 as uuidv4 } from "uuid";
import { KnowledgeSourceSelector } from "../../../components/knowledge";
import { KnowledgeApi } from "../../../lib/knowledgeApi";
import { ExtendedNodeData, SourceUploadResult } from "../../../types/knowledge";
import { ErrorBoundary } from "../../../components/ErrorBoundary";
import { LoadingSpinner } from "../../../components/LoadingSpinner";

interface NodeParam {
  id: string;
  name: string;
  description: string;
  value?: string;
}

interface NodeData {
  id: string;
  label: string;
  type: "message" | "webhook" | "knowledge" | "conditional_llm" | "forced_message";
  action?: string;
  url?: string;
  method?: string;
  params?: NodeParam[];
  missing_param_message?: string;
  // Conditional LLM specific properties
  branches?: { id: string; condition_text: string; next_node?: string }[];
  default_branch?: string;
  // Legacy filename property for backward compatibility
  filename?: string;
  // Forced message specific properties
  forced_text?: string;
}

// Use ExtendedNodeData for the actual node data with knowledge properties

export default function AgentEditorPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.id as string;

  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [agentName, setAgentName] = useState("");
  const [loading, setLoading] = useState(true);
  const [startNodeId, setStartNodeId] = useState<string | null>(null); // Track start node

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editNode, setEditNode] = useState<ExtendedNodeData | null>(null);

  // Legacy file upload state for backward compatibility
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  // Context menu state
  const [contextMenu, setContextMenu] = useState<{x: number, y: number, nodeId: string} | null>(null);
  
  // Knowledge source management
  const [knowledgeError, setKnowledgeError] = useState<string | null>(null);
  const [knowledgeLoading, setKnowledgeLoading] = useState(false);

  // Memoize nodeTypes to prevent recreation on every render
  const nodeTypes = useMemo(() => {
    // Custom node component wrapper that includes start node info
    const CustomNodeWrapper = (props: any) => {
      return <CustomNode {...props} isStartNode={props.id === startNodeId} />;
    };
    
    return { custom: CustomNodeWrapper };
  }, [startNodeId]);

  // Function to get knowledge node information with enhanced data
  const fetchKnowledgeInfo = async (agentId: string, nodeId: string): Promise<ExtendedNodeData | null> => {
    try {
      const knowledgeInfo = await KnowledgeApi.getKnowledgeInfo(agentId, nodeId);
      if (knowledgeInfo) {
        return {
          id: nodeId,
          label: knowledgeInfo.name || 'Knowledge Node',
          type: 'knowledge',
          source_type: knowledgeInfo.source_type,
          source_name: knowledgeInfo.name,
          source_metadata: knowledgeInfo.source_data,
          extractor_metadata: knowledgeInfo.extractor_metadata,
          embeddings_count: knowledgeInfo.embeddings_count,
          updated_at: knowledgeInfo.updated_at,
          // Legacy filename for backward compatibility
          filename: knowledgeInfo.name
        };
      }
    } catch (err) {
      console.log("Knowledge info not found for node:", nodeId);
    }
    return null;
  };


  const onNodesChange = (changes: NodeChange[]) =>
    setNodes((nds) => applyNodeChanges(changes, nds));
  const onEdgesChange = (changes: EdgeChange[]) =>
    setEdges((eds) => applyEdgeChanges(changes, eds));
  const onConnect = (connection: Edge | Connection) =>
    setEdges((eds) => addEdge(connection, eds));
  const onNodesDelete = (deleted: Node[]) => {
    setNodes((nds) => nds.filter((n) => !deleted.find((d) => d.id === n.id)));
    setEdges((eds) =>
      eds.filter(
        (e) => !deleted.find((d) => d.id === e.source || d.id === e.target)
      )
    );
  };
  const onEdgesDelete = (deleted: Edge[]) => {
    setEdges((eds) => eds.filter((e) => !deleted.find((d) => d.id === e.id)));
  };

  const onNodeContextMenu = (event: React.MouseEvent, node: Node) => {
    event.preventDefault();
    setContextMenu({
      x: event.clientX,
      y: event.clientY,
      nodeId: node.id
    });
  };

  const setAsStartNode = (nodeId: string) => {
    setStartNodeId(nodeId);
    setContextMenu(null);
  };

  const closeContextMenu = () => {
    setContextMenu(null);
  };

  const openModal = async (node: Node) => {
    if (node.data.type === 'knowledge') {
      // Load enhanced knowledge data
      const knowledgeData = await fetchKnowledgeInfo(agentId, node.id);
      if (knowledgeData) {
        setEditNode(knowledgeData);
      } else {
        // Fallback to basic node data if knowledge info is not available
        setEditNode({ ...node.data, id: node.id } as ExtendedNodeData);
      }
    } else {
      setEditNode({ ...node.data, id: node.id } as ExtendedNodeData);
    }
    setKnowledgeError(null);
    setIsModalOpen(true);
  };

  useEffect(() => {
    async function loadAgent() {
      try {
        const data = await apiFetch(`/agents/${agentId}`);
        setAgentName(data.name);

        if (data.logic) {
          const agentNodes: Node[] = [];
          
          // Проходим по всем нодам и создаем объекты
          for (let i = 0; i < data.logic.nodes.length; i++) {
            const n = data.logic.nodes[i];
            let paramsArray: NodeParam[] = [];
            if (n.type === "webhook" && n.params) {
              paramsArray = n.params.map((el: any) => ({
                ...el,
                id: uuidv4(),
              }));
            }

            // For knowledge nodes, get enhanced information
            let nodeData: any = {
              label: n.text || n.name || "Node",
              type: n.type,
              params: paramsArray,
              action: n.action,
              url: n.url,
              method: n.method,
              missing_param_message: n.missing_param_message,
            };

            // Handle conditional LLM specific properties
            if (n.type === "conditional_llm") {
              nodeData.branches = n.branches || [];
              nodeData.default_branch = n.default_branch;
            }

            // Handle forced message specific properties
            if (n.type === "forced_message") {
              nodeData.forced_text = n.forced_text;
              console.log(`Loading forced_message node ${n.id} with forced_text:`, n.forced_text);
            }

            if (n.type === "knowledge") {
              const knowledgeData = await fetchKnowledgeInfo(agentId, n.id);
              if (knowledgeData) {
                // Merge knowledge data with base node data
                nodeData = {
                  ...nodeData,
                  source_type: knowledgeData.source_type,
                  source_name: knowledgeData.source_name,
                  source_metadata: knowledgeData.source_metadata,
                  extractor_metadata: knowledgeData.extractor_metadata,
                  embeddings_count: knowledgeData.embeddings_count,
                  updated_at: knowledgeData.updated_at,
                  filename: knowledgeData.source_name, // Legacy compatibility
                };
              }
            }

            agentNodes.push({
              id: n.id,
              type: "custom",
              data: nodeData,
              position: n.position || { x: i * 200, y: 100 },
            });
          }

          const agentEdges: Edge[] = [];
          data.logic.nodes.forEach((n: any) => {
            if (n.type === "message" && n.next) {
              agentEdges.push({
                id: `${n.id}->${n.next}`,
                source: n.id,
                target: n.next,
                sourceHandle: "default",
              });
            }
            if (n.type === "forced_message" && n.next) {
              agentEdges.push({
                id: `${n.id}->${n.next}`,
                source: n.id,
                target: n.next,
                sourceHandle: "default",
              });
            }
            if (n.type === "knowledge" && n.next) {
              agentEdges.push({
                id: `${n.id}->${n.next}`,
                source: n.id,
                target: n.next,
                sourceHandle: "default",
              });
            }
            if (n.type === "conditional_llm") {
              // Handle conditional branches
              if (n.branches) {
                n.branches.forEach((branch: any) => {
                  if (branch.next_node) {
                    agentEdges.push({
                      id: `${n.id}->${branch.next_node}`,
                      source: n.id,
                      target: branch.next_node,
                      sourceHandle: branch.id,
                    });
                  }
                });
              }
              // Handle default branch
              if (n.default_branch) {
                agentEdges.push({
                  id: `${n.id}->${n.default_branch}`,
                  source: n.id,
                  target: n.default_branch,
                  sourceHandle: "default",
                });
              }
            }
            if (n.type === "webhook") {
              if (n.on_success) {
                agentEdges.push({
                  id: `${n.id}->${n.on_success}`,
                  source: n.id,
                  target: n.on_success,
                  sourceHandle: "success",
                });
              }
              if (n.on_failure) {
                agentEdges.push({
                  id: `${n.id}->${n.on_failure}`,
                  source: n.id,
                  target: n.on_failure,
                  sourceHandle: "failure",
                });
              }
            }
          });

          setNodes(agentNodes);
          setEdges(agentEdges);
          setStartNodeId(data.logic.start_node || null); // Load start node
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadAgent();
  }, [agentId]);

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      if (contextMenu) {
        setContextMenu(null);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [contextMenu]);

  // Knowledge source upload handlers
  const handleKnowledgeUploadSuccess = async (result: SourceUploadResult) => {
    setKnowledgeLoading(true);
    try {
      // Reload knowledge data for the node
      if (editNode) {
        const updatedKnowledgeData = await fetchKnowledgeInfo(agentId, editNode.id);
        if (updatedKnowledgeData) {
          setEditNode(updatedKnowledgeData);
        }
        
        // Update the node in the graph
        setNodes((nds) => 
          nds.map((n) => {
            if (n.id === editNode.id && updatedKnowledgeData) {
              return {
                ...n,
                data: updatedKnowledgeData
              };
            }
            return n;
          })
        );
        
        setKnowledgeError(null);
        alert(`Successfully added ${result.source_type} source!`);
      }
    } catch (error) {
      setKnowledgeError(error instanceof Error ? error.message : 'Failed to update node');
    } finally {
      setKnowledgeLoading(false);
    }
  };

  const handleKnowledgeUploadError = (error: string) => {
    setKnowledgeError(error);
    setKnowledgeLoading(false);
  };

  const addNode = () => {
    const newId = uuidv4();
    const newNode: Node = {
      id: newId,
      type: "custom",
      data: { id: newId, label: "New Node", type: "message", params: [] } as ExtendedNodeData,
      position: { x: nodes.length * 250, y: 100 },
    };
    setNodes((prev) => [...prev, newNode]);
    openModal(newNode);
  };
  const saveNode = async () => {
    if (!editNode) return;

    console.log("Saving node:", editNode.type);
    console.log("Node data before save:", editNode);
    
    // For knowledge nodes, we don't need to handle file upload here anymore
    // The KnowledgeSourceSelector component handles uploads directly
    
    // Legacy file upload support for backward compatibility
    if (editNode.type === "knowledge" && selectedFile) {
      console.log("Legacy file upload");
      const formData = new FormData();
      formData.append("file", selectedFile);

      try {
        const uploadResponse = await apiFetch(`/knowledge/upload/${agentId}/${editNode.id}`, {
          method: "POST",
          body: formData,
        });
        
        // Update filename in editNode after successful upload
        editNode.filename = uploadResponse.filename;
        editNode.source_name = uploadResponse.filename;
        editNode.source_type = 'file';
        
        alert("File uploaded successfully!");
      } catch (err) {
        console.error(err);
        alert("Error uploading file");
        return; // Stop saving node if file upload failed
      }
    }

    // Debug forced message data
    if (editNode.type === "forced_message") {
      console.log("Saving forced message with text:", editNode.forced_text);
    }

    // Update nodes in state
    setNodes((nds) => {
      const existing = nds.find((n) => n.id === editNode.id);
      if (existing) {
        console.log("Updating existing node:", editNode.id);
        return nds.map((n) =>
          n.id === editNode.id ? { ...n, data: { ...editNode } } : n
        );
      }
      const newId = editNode.id || uuidv4();
      console.log("Creating new node:", newId);
      return [
        ...nds,
        {
          id: newId,
          type: "custom",
          data: { ...editNode, id: newId },
          position: { x: nds.length * 250, y: 100 },
        },
      ];
    });

    setIsModalOpen(false);
  };


  const saveToServer = async () => {
    try {
      const outgoing = edges.reduce<Record<string, Edge[]>>((acc, e) => {
        acc[e.source] = acc[e.source] || [];
        acc[e.source].push(e);
        return acc;
      }, {});

      const allTargets = new Set(edges.map((e) => e.target));
      let startNode = null;
      
      // Use manually selected start node if available
      if (startNodeId && nodes.find(n => n.id === startNodeId)) {
        startNode = nodes.find(n => n.id === startNodeId);
        console.log("Using manually selected start node:", startNode?.id);
      } else {
        // Fallback to automatic detection
        startNode = nodes.find((n) => !allTargets.has(n.id));
        
        // If no start node found (all nodes are targets in a cycle), use the first node
        if (!startNode && nodes.length > 0) {
          startNode = nodes[0];
          console.log("No natural start node found (likely cyclic graph), using first node:", startNode.id);
        }
      }

      const logicNodes = nodes.map((n) => {
        const data = n.data as NodeData;
        const base: any = {
          id: n.id,
          type: data.type,
          text: data.label,
        };

        if (data.type === "message" || data.type === "knowledge" || data.type === "forced_message") {
          const out = outgoing[n.id]?.[0];
          if (out) base.next = out.target;
        }

        if (data.type === "forced_message") {
          console.log("Processing forced_message node:", n.id, "with data:", data);
          if (data.forced_text) {
            base.forced_text = data.forced_text;
            console.log("Added forced_text to base:", data.forced_text);
          } else {
            console.log("WARNING: No forced_text found for forced_message node");
          }
        }

        if (data.type === "conditional_llm") {
          if (data.branches && data.branches.length > 0) {
            // Map each branch to its connected edge
            base.branches = data.branches.map((branch) => {
              const branchEdge = outgoing[n.id]?.find((edge) => edge.sourceHandle === branch.id);
              return {
                id: branch.id,
                condition_text: branch.condition_text,
                next_node: branchEdge?.target || null
              };
            });
          }
          
          if (data.default_branch) {
            const defaultEdge = outgoing[n.id]?.find((edge) => edge.sourceHandle === "default");
            base.default_branch = defaultEdge?.target || null;
          }
        }

        if (data.type === "webhook") {
          if (data.action) base.action = data.action;
          if (data.url) base.url = data.url;
          if (data.method) base.method = data.method;
          if (data.missing_param_message)
            base.missing_param_message = data.missing_param_message;
          if (data.params && data.params.length > 0) {
            base.params = data.params;
          }
          const outs = outgoing[n.id] || [];
          outs.forEach((edge) => {
            if (edge.sourceHandle === "success") base.on_success = edge.target;
            else if (edge.sourceHandle === "failure") base.on_failure = edge.target;
          });
        }
        base.position = n.position;
        return base;
      });

      const payload = {
        logic: {
          nodes: logicNodes,
          start_node: startNode?.id || null,
        },
      };

      console.log("SAVE PAYLOAD:", payload);
      console.log("Start node:", startNode?.id);
      console.log("Nodes count:", logicNodes.length);
      console.log("Node IDs:", logicNodes.map(n => n.id));
      await apiFetch(`/agents/${agentId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      alert("Логика агента успешно сохранена!");
    } catch (err) {
      console.error(err);
      alert("Ошибка при сохранении на сервер");
    }
  };

  if (loading) return <div className="p-4">Загрузка...</div>;

  return (
    <ReactFlowProvider>
      <div className="h-screen flex flex-col bg-gray-100 p-4">
        <div className="flex justify-between items-center mb-2">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push("/")}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <span className="text-xl">←</span>
              <span>К списку агентов</span>
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Редактор агента: {agentName}
              </h1>
              {startNodeId && (
                <p className="text-sm text-green-600 mt-1">
                  🚀 Start Node: <span className="font-mono bg-green-100 px-2 py-1 rounded">{startNodeId}</span>
                </p>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            <Link
              href={`/agents/${agentId}/chat`}
              className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 flex items-center gap-2"
            >
              <span>💬</span>
              <span>Открыть чат</span>
            </Link>
            <button
              className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
              onClick={addNode}
            >
              Добавить узел
            </button>
            <button
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              onClick={saveToServer}
            >
              Сохранить на сервер
            </button>
          </div>
        </div>

        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodesDelete={onNodesDelete}
          onEdgesDelete={onEdgesDelete}
          onConnect={onConnect}
          fitView
          onNodeDoubleClick={(event, node) => {
            event.stopPropagation();
            openModal(node);
          }}
          onNodeContextMenu={onNodeContextMenu}
          onPaneClick={closeContextMenu}
          nodeTypes={nodeTypes}
        >
          <MiniMap />
          <Controls />
          <Background />
          
          {/* Context Menu */}
          {contextMenu && (
            <div
              className="fixed z-50 bg-white border border-gray-300 rounded-lg shadow-lg py-1 min-w-[150px]"
              style={{ left: contextMenu.x, top: contextMenu.y }}
              onClick={closeContextMenu}
            >
              <button
                className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center gap-2"
                onClick={(e) => {
                  e.stopPropagation();
                  setAsStartNode(contextMenu.nodeId);
                }}
              >
                <span className="text-green-600">🚀</span>
                Set as Start Node
              </button>
              {startNodeId === contextMenu.nodeId && (
                <div className="px-4 py-2 text-sm text-green-600 font-medium">
                  ✓ Current Start Node
                </div>
              )}
            </div>
          )}
        </ReactFlow>

        {/* --- Модалка --- */}
        <Dialog
          open={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          className="fixed z-10 inset-0 overflow-y-auto"
        >
          <div className="flex items-center justify-center min-h-screen px-4">
            <Dialog.Panel className="bg-white rounded shadow-lg p-6 w-full max-w-md">
              <Dialog.Title className="text-xl font-bold mb-4">
                Редактировать узел
              </Dialog.Title>
              {editNode && (
                <>
                  <label className="block mb-2 text-gray-800">Текст узла</label>
                  <input
                    type="text"
                    value={editNode.label}
                    onChange={(e) =>
                      setEditNode({ ...editNode, label: e.target.value })
                    }
                    className="w-full p-2 border rounded mb-4 text-gray-900 placeholder-gray-500"
                  />

                  <label className="block mb-2 text-gray-800">Тип узла</label>
                  <select
                    value={editNode.type}
                    onChange={(e) =>
                      setEditNode({
                        ...editNode,
                        type: e.target.value as "message" | "webhook" | "knowledge" | "conditional_llm" | "forced_message",
                      })
                    }
                    className="w-full p-2 border rounded mb-4 text-gray-900"
                  >
                    <option value="message">Message</option>
                    <option value="webhook">Webhook</option>
                    <option value="knowledge">Knowledge</option>
                    <option value="conditional_llm">Conditional LLM</option>
                    <option value="forced_message">Forced Message</option>
                  </select>

                  {editNode.type === "webhook" && (
                    <>
                      <div className="mb-4">
                        <h3 className="font-semibold mb-2 text-gray-800">
                          Параметры Webhook
                        </h3>
                        {(editNode.params || []).map((param) => (
                          <div key={param.id} className="flex gap-2 mb-2">
                            <input
                              type="text"
                              placeholder="Название"
                              className="flex-1 p-2 border rounded text-gray-900"
                              value={param.name}
                              onChange={(e) => {
                                const newParams = [...(editNode.params || [])];
                                const idx = newParams.findIndex((p) => p.id === param.id);
                                newParams[idx].name = e.target.value;
                                setEditNode({ ...editNode, params: newParams });
                              }}
                            />
                            <input
                              type="text"
                              placeholder="Описание"
                              className="flex-2 p-2 border rounded text-gray-900"
                              value={param.description}
                              onChange={(e) => {
                                const newParams = [...(editNode.params || [])];
                                const idx = newParams.findIndex((p) => p.id === param.id);
                                newParams[idx].description = e.target.value;
                                setEditNode({ ...editNode, params: newParams });
                              }}
                            />
                            <input
                              type="text"
                              placeholder="Фиксированное значение (опционально)"
                              className="flex-2 p-2 border rounded text-gray-900"
                              value={param.value || ""}
                              onChange={(e) => {
                                const newParams = [...(editNode.params || [])];
                                const idx = newParams.findIndex((p) => p.id === param.id);
                                newParams[idx].value = e.target.value;
                                setEditNode({ ...editNode, params: newParams });
                              }}
                            />
                            <button
                              type="button"
                              className="bg-red-500 text-white px-2 rounded hover:bg-red-600"
                              onClick={() => {
                                const newParams = [...(editNode.params || [])].filter((p) => p.id !== param.id);
                                setEditNode({ ...editNode, params: newParams });
                              }}
                            >
                              ×
                            </button>
                          </div>
                        ))}
                        <button
                          type="button"
                          className="bg-green-500 text-white px-4 py-1 rounded hover:bg-green-600"
                          onClick={() => {
                            const newParams = [
                              ...(editNode.params || []),
                              { id: uuidv4(), name: "", description: "", value: "" },
                            ];
                            setEditNode({ ...editNode, params: newParams });
                          }}
                        >
                          Добавить параметр
                        </button>

                        <label className="block mb-1 text-gray-800 mt-2">Action</label>
                        <input
                          type="text"
                          className="w-full p-2 border rounded mb-2 text-gray-900"
                          value={editNode.action || ""}
                          onChange={(e) =>
                            setEditNode({ ...editNode, action: e.target.value })
                          }
                        />
                        <label className="block mb-1 text-gray-800">URL</label>
                        <input
                          type="text"
                          className="w-full p-2 border rounded mb-2 text-gray-900"
                          value={editNode.url || ""}
                          onChange={(e) =>
                            setEditNode({ ...editNode, url: e.target.value })
                          }
                        />
                        <label className="block mb-1 text-gray-800">Method</label>
                        <select
                          className="w-full p-2 border rounded mb-2 text-gray-900"
                          value={editNode.method || "POST"}
                          onChange={(e) =>
                            setEditNode({ ...editNode, method: e.target.value })
                          }
                        >
                          <option value="POST">POST</option>
                          <option value="GET">GET</option>
                        </select>
                        <label className="block mb-1 text-gray-800">
                          Сообщение при нехватке параметров
                        </label>
                        <input
                          type="text"
                          className="w-full p-2 border rounded mb-2 text-gray-900"
                          value={editNode.missing_param_message || ""}
                          onChange={(e) =>
                            setEditNode({
                              ...editNode,
                              missing_param_message: e.target.value,
                            })
                          }
                        />
                      </div>
                    </>
                  )}

                  {editNode.type === "conditional_llm" && (
                    <div className="mb-4">
                      <h3 className="font-semibold mb-2 text-gray-800">
                        Conditional Branches Configuration
                      </h3>
                      <p className="text-sm text-gray-600 mb-4">
                        Create multiple branches with conditions. The LLM will evaluate user input and choose the most appropriate branch.
                      </p>
                      
                      {(editNode.branches || []).map((branch, index) => (
                        <div key={branch.id} className="mb-3 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <label className="text-sm font-medium text-purple-800">
                              Branch {index + 1}
                            </label>
                            <button
                              type="button"
                              className="bg-red-500 text-white px-2 py-1 rounded text-xs hover:bg-red-600"
                              onClick={() => {
                                const newBranches = [...(editNode.branches || [])].filter((b) => b.id !== branch.id);
                                setEditNode({ ...editNode, branches: newBranches });
                              }}
                            >
                              Remove
                            </button>
                          </div>
                          <textarea
                            placeholder="Describe the condition for this branch (e.g., 'User wants to place an order', 'User has a question about products')"
                            className="w-full p-2 border rounded text-gray-900 text-sm"
                            rows={2}
                            value={branch.condition_text}
                            onChange={(e) => {
                              const newBranches = [...(editNode.branches || [])];
                              const idx = newBranches.findIndex((b) => b.id === branch.id);
                              newBranches[idx].condition_text = e.target.value;
                              setEditNode({ ...editNode, branches: newBranches });
                            }}
                          />
                        </div>
                      ))}
                      
                      <button
                        type="button"
                        className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600 text-sm"
                        onClick={() => {
                          const newBranches = [
                            ...(editNode.branches || []),
                            { id: uuidv4(), condition_text: "", next_node: undefined },
                          ];
                          setEditNode({ ...editNode, branches: newBranches });
                        }}
                      >
                        Add Branch
                      </button>
                      
                      <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Default Branch (optional)
                        </label>
                        <p className="text-xs text-gray-500 mb-2">
                          This branch will be taken if none of the conditions match
                        </p>
                        <input
                          type="text"
                          placeholder="Default branch node ID (leave empty for no default)"
                          className="w-full p-2 border rounded text-gray-900 text-sm"
                          value={editNode.default_branch || ""}
                          onChange={(e) =>
                            setEditNode({ ...editNode, default_branch: e.target.value || undefined })
                          }
                        />
                      </div>
                    </div>
                  )}

                  {editNode.type === "forced_message" && (
                    <div className="mb-4">
                      <label className="block mb-2 text-gray-800">Принудительное сообщение</label>
                      <textarea
                        value={editNode.forced_text || ""}
                        onChange={(e) => {
                          console.log("Forced text changing to:", e.target.value);
                          setEditNode({ ...editNode, forced_text: e.target.value });
                        }}
                        className="w-full p-2 border rounded mb-4 text-gray-900 placeholder-gray-500"
                        rows={3}
                        placeholder="Введите текст сообщения, которое будет отправлено автоматически..."
                      />
                      <p className="text-xs text-gray-500">
                        Это сообщение будет отправлено автоматически без ожидания ввода пользователя.
                      </p>
                      <p className="text-xs text-blue-600 mt-1">
                        Current value: "{editNode.forced_text || "(empty)"}"
                      </p>
                    </div>
                  )}

                  {editNode.type === "knowledge" && (
                    <div className="mb-4">
                      <h3 className="font-semibold mb-4 text-gray-800">Knowledge Source Configuration</h3>
                      
                      {/* Show current source info if available */}
                      {editNode.source_type && editNode.source_name && (
                        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                          <div className="flex items-center space-x-2">
                            <span className="text-lg">
                              {editNode.source_type === 'web' ? '🌐' : 
                               editNode.source_type === 'audio' ? '🎵' : '📄'}
                            </span>
                            <div>
                              <div className="font-medium text-green-800">
                                Current Source: {editNode.source_name}
                              </div>
                              <div className="text-sm text-green-600">
                                Type: {editNode.source_type} • 
                                {editNode.updated_at ? 
                                  `Updated: ${new Date(editNode.updated_at).toLocaleDateString()}` : 
                                  'Recently added'
                                }
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {/* Knowledge Error Display */}
                      {knowledgeError && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800">
                          {knowledgeError}
                        </div>
                      )}
                      
                      {/* Knowledge Source Selector */}
                      <ErrorBoundary
                        fallback={
                          <div className="p-4 border border-yellow-300 rounded-lg bg-yellow-50">
                            <p className="text-yellow-800">Unable to load knowledge source options. Please try refreshing the page.</p>
                          </div>
                        }
                      >
                        {knowledgeLoading ? (
                          <LoadingSpinner size="md" text="Processing..." className="py-4" />
                        ) : (
                          <KnowledgeSourceSelector
                            agentId={agentId}
                            nodeId={editNode.id}
                            onUploadSuccess={handleKnowledgeUploadSuccess}
                            onError={handleKnowledgeUploadError}
                          />
                        )}
                      </ErrorBoundary>
                      
                      {/* Legacy file upload for backward compatibility */}
                      <div className="mt-6 pt-4 border-t border-gray-200">
                        <details className="group">
                          <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                            📁 Legacy File Upload (for backward compatibility)
                          </summary>
                          <div className="mt-2">
                            <label className="block mb-1 text-gray-800 text-sm">Legacy File Upload</label>
                            <input
                              type="file"
                              className="w-full mb-2 text-sm"
                              onChange={(e) => {
                                if (e.target.files?.[0]) {
                                  setSelectedFile(e.target.files?.[0] || null);
                                  console.log("File selected for legacy upload:", e.target.files[0]);
                                }
                              }}
                            />
                            <p className="text-xs text-gray-500">
                              Note: Use the source selector above for better experience
                            </p>
                          </div>
                        </details>
                      </div>
                    </div>
                  )}


                  <div className="flex justify-end gap-2 mt-2">
                    <button
                      className="bg-gray-300 px-4 py-2 rounded hover:bg-gray-400"
                      onClick={() => setIsModalOpen(false)}
                    >
                      Отмена
                    </button>
                    <button
                      className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                      onClick={saveNode}
                    >
                      Сохранить
                    </button>
                  </div>
                </>
              )}
            </Dialog.Panel>
          </div>
        </Dialog>
      </div>
    </ReactFlowProvider>
  );
}