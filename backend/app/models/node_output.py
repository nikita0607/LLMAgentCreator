from sqlalchemy import Column, Integer, ForeignKey, DateTime, func, String, Text
from sqlalchemy.orm import relationship
from app.db import Base

class NodeOutput(Base):
    __tablename__ = "node_output"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agent.id"), nullable=False)
    node_id = Column(String, nullable=False)  # ID of the node that generated this output
    node_type = Column(String, nullable=False)  # Type of node (llm_request, knowledge, webhook)
    output_text = Column(Text, nullable=False)  # Full output text from the node
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to agent
    agent = relationship("Agent", backref="node_outputs")