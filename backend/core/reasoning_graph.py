import asyncio
import logging
import time
import uuid
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger("friday.core.reasoning")

class ReasoningNode:
    """Represents a single step in a reasoning graph."""
    def __init__(self, node_id: str, type: str, action: Callable, metadata: Dict[str, Any] = None):
        self.node_id = node_id
        self.type = type # inference, tool, memory, validation
        self.action = action
        self.metadata = metadata or {}
        self.status = "pending" # pending, running, success, failed
        self.result = None
        self.duration = 0
        self.retries = 0

    async def run(self, context: Dict[str, Any]):
        self.status = "running"
        start = time.time()
        try:
            if asyncio.iscoroutinefunction(self.action):
                self.result = await self.action(context)
            else:
                self.result = await asyncio.to_thread(self.action, context)
            self.status = "success"
        except Exception as e:
            logger.error(f"Node {self.node_id} failed: {e}")
            self.status = "failed"
            self.result = str(e)
        finally:
            self.duration = time.time() - start

class ReasoningGraph:
    """Directed graph for non-linear cognitive execution."""
    def __init__(self, graph_id: str = None):
        self.graph_id = graph_id or str(uuid.uuid4())[:8]
        self.nodes: Dict[str, ReasoningNode] = {}
        self.edges: List[tuple] = [] # (from_id, to_id)
        self.context: Dict[str, Any] = {}
        self.scratchpad: List[str] = []

    def add_node(self, node: ReasoningNode):
        self.nodes[node.node_id] = node

    def add_edge(self, from_id: str, to_id: str):
        self.edges.append((from_id, to_id))

    async def execute(self, initial_context: Dict[str, Any]):
        """Executes nodes in topological order (simplified for now)."""
        self.context = initial_context
        logger.info(f"ReasoningGraph {self.graph_id}: Execution STARTED")
        
        # Simple linear execution for now, to be expanded to full DAG
        for node_id, node in self.nodes.items():
            logger.debug(f"Executing Node: {node_id} ({node.type})")
            await node.run(self.context)
            
            # Update shared context with result
            self.context[f"result_{node_id}"] = node.result
            
            if node.status == "failed" and node.metadata.get("critical", True):
                logger.error(f"Graph failed at critical node {node_id}")
                break
                
        logger.info(f"ReasoningGraph {self.graph_id}: Execution FINISHED")
        return self.context
