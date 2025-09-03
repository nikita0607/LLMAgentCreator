"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
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

interface NodeParam {
  id: string;
  name: string;
  description: string;
  value?: string;
}

interface NodeData {
  id: string;
  label: string;
  type: "message" | "webhook" | "knowledge";
  action?: string;
  url?: string;
  method?: string;
  params?: NodeParam[];
  missing_param_message?: string;
}

const nodeTypes = { custom: CustomNode };

export default function AgentEditorPage() {
  const params = useParams();
  const agentId = params.id;

  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [agentName, setAgentName] = useState("");
  const [loading, setLoading] = useState(true);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editNode, setEditNode] = useState<NodeData | null>(null);

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

  const openModal = (node: Node) => {
    const fullNode = nodes.find((n) => n.id === node.id);
    if (fullNode) {
      setEditNode({ ...fullNode.data, id: fullNode.id });
    } else {
      setEditNode({ ...node.data, id: node.id });
    }
    setIsModalOpen(true);
  };

  useEffect(() => {
    async function loadAgent() {
      try {
        const data = await apiFetch(`/agents/${agentId}`);
        setAgentName(data.name);

        if (data.logic) {
          const agentNodes: Node[] = data.logic.nodes.map((n: any, i: number) => {
            let paramsArray: NodeParam[] = [];
            if (n.type === "webhook" && n.params) {
              paramsArray = n.params.map((el: any) => ({
                ...el,
                id: uuidv4(),
              }));
            }

            return {
              id: n.id,
              type: "custom",
              data: {
                label: n.text || n.name || "Node",
                type: n.type,
                params: paramsArray,
                action: n.action,
                url: n.url,
                method: n.method,
                missing_param_message: n.missing_param_message,
              },
              position: n.position || { x: i * 200, y: 100 },
            };
          });

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
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadAgent();
  }, [agentId]);

  const addNode = () => {
    const newId = uuidv4();
    const newNode: Node = {
      id: newId,
      type: "custom",
      data: { id: newId, label: "Новый узел", type: "message", params: [] },
      position: { x: nodes.length, y: 100 },
    };
    setNodes((prev) => [...prev, newNode]);
    openModal(newNode);
  };

  const saveNode = () => {
    if (!editNode) return;
    setNodes((nds) => {
      const existing = nds.find((n) => n.id === editNode.id);
      if (existing) {
        return nds.map((n) =>
          n.id === editNode.id ? { ...n, data: { ...editNode } } : n
        );
      }
      const newId = editNode.id || uuidv4();
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
      const startNode = nodes.find((n) => !allTargets.has(n.id));

      const logicNodes = nodes.map((n) => {
        const data = n.data as NodeData;
        const base: any = {
          id: n.id,
          type: data.type,
          text: data.label,
        };

        if (data.type === "message" || data.type === "knowledge") {
          const out = outgoing[n.id]?.[0];
          if (out) base.next = out.target;
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
          <h1 className="text-2xl font-bold text-gray-900">
            Редактор агента: {agentName}
          </h1>
          <div className="flex gap-2">
            <Link
              href="/"
              className="bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300"
            >
              К списку агентов
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
          nodeTypes={nodeTypes}
        >
          <MiniMap />
          <Controls />
          <Background />
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
                        type: e.target.value as "message" | "webhook" | "knowledge",
                      })
                    }
                    className="w-full p-2 border rounded mb-4 text-gray-900"
                  >
                    <option value="message">Message</option>
                    <option value="webhook">Webhook</option>
                    <option value="knowledge">Knowledge</option>
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