import asyncio
import uuid
import json
import logging
import sys
import time
from typing import Dict, Any, List, Set, Tuple, Optional, Callable
from datetime import datetime

logger = logging.getLogger("friday.core.execution_graph")

class NodeStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"

class ExecutionNode:
    def __init__(self, node_id: str, node_type: str, action: Callable[..., Any], args: Dict[str, Any] = None, max_retries: int = 2):
        self.id = node_id
        self.node_type = node_type
        self.action = action
        self.args = args or {}
        self.status = NodeStatus.PENDING
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.retry_count = 0
        self.max_retries = max_retries
        self.dependencies: Set[str] = set()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.node_type,
            "status": self.status,
            "args": self.args,
            "retry_count": self.retry_count,
            "error": self.error
        }

class ExecutionGraph:
    """
    directed acyclic graph managing scheduling, checkpointing, rollbacks, 
    and transaction integrity for multi-step agent actions.
    """
    def __init__(self, graph_id: str = None):
        self.id = graph_id or str(uuid.uuid4())
        self.nodes: Dict[str, ExecutionNode] = {}
        self.edges: List[Tuple[str, str]] = []  # (source, target) -> target depends on source
        self.checkpoints: List[Dict[str, Any]] = []
        self.created_at = datetime.now().isoformat()
        self.state: Dict[str, Any] = {}

    def add_node(self, node: ExecutionNode):
        self.nodes[node.id] = node

    def add_edge(self, source_id: str, target_id: str):
        if source_id in self.nodes and target_id in self.nodes:
            self.edges.append((source_id, target_id))
            self.nodes[target_id].dependencies.add(source_id)

    def create_checkpoint(self, name: str):
        """Creates a serialized snapshot of the current node states."""
        snapshot = {
            "checkpoint_name": name,
            "timestamp": time.time() if "time" in sys.modules else datetime.now().isoformat(),
            "nodes": {nid: node.status for nid, node in self.nodes.items()},
            "state": self.state.copy()
        }
        self.checkpoints.append(snapshot)
        logger.info(f"ExecutionGraph Checkpoint '{name}' created for graph {self.id}")

    def rollback_to_checkpoint(self, name: str):
        """Reverts node statuses to a saved checkpoint."""
        for cp in reversed(self.checkpoints):
            if cp["checkpoint_name"] == name:
                for nid, status in cp["nodes"].items():
                    if nid in self.nodes:
                        self.nodes[nid].status = status
                        if status == NodeStatus.PENDING:
                            self.nodes[nid].result = None
                            self.nodes[nid].error = None
                self.state = cp["state"].copy()
                logger.warning(f"ExecutionGraph Rolled Back to checkpoint '{name}' for graph {self.id}")
                return
        logger.error(f"Checkpoint '{name}' not found for rollback.")

    async def execute(self) -> bool:
        """
        Asynchronously executes the graph in topological order.
        Resolves node dependencies dynamically.
        """
        self.create_checkpoint("initial")
        
        while not self.is_complete():
            runnable_nodes = self.get_runnable_nodes()
            if not runnable_nodes and not self.has_running_nodes():
                # Cycle detected or deadlock
                logger.error("Deadlock or circular dependency detected in graph execution.")
                return False
                
            if not runnable_nodes:
                await asyncio.sleep(0.1)
                continue
                
            tasks = [self._execute_node(node) for node in runnable_nodes]
            await asyncio.gather(*tasks)
            
        return self.is_success()

    async def _execute_node(self, node: ExecutionNode):
        node.status = NodeStatus.RUNNING
        logger.info(f"GraphNode Execution Started: {node.node_type}:{node.id}")
        
        # Populate input args from dependencies' outputs
        resolved_args = node.args.copy()
        for dep_id in node.dependencies:
            dep_node = self.nodes[dep_id]
            if dep_node.result:
                resolved_args[f"dep_{dep_node.id}"] = dep_node.result

        while node.retry_count <= node.max_retries:
            try:
                # Handle async or sync actions natively
                if asyncio.iscoroutinefunction(node.action):
                    result = await node.action(**resolved_args)
                else:
                    result = await asyncio.to_thread(node.action, **resolved_args)
                
                node.result = result
                node.status = NodeStatus.SUCCESS
                logger.info(f"GraphNode Execution SUCCESS: {node.id}")
                break
            except Exception as e:
                node.retry_count += 1
                node.error = str(e)
                logger.warning(f"GraphNode Execution Failed: {node.id} (Attempt {node.retry_count}/{node.max_retries}). Error: {e}")
                
                from core.event_bus import event_bus
                event_bus.emit("brain", "action_retry", {"tool": node.node_type, "attempt": node.retry_count, "max": node.max_retries, "error": str(e)})
                
                if node.retry_count > node.max_retries:
                    node.status = NodeStatus.FAILED
                    # Attempt local rollback if needed
                    self.rollback_to_checkpoint("initial")
                    break
                await asyncio.sleep(0.5 * node.retry_count)

    def get_runnable_nodes(self) -> List[ExecutionNode]:
        runnable = []
        for node in self.nodes.values():
            if node.status != NodeStatus.PENDING:
                continue
            # Check dependencies
            deps_ok = True
            for dep_id in node.dependencies:
                dep_node = self.nodes[dep_id]
                if dep_node.status != NodeStatus.SUCCESS:
                    deps_ok = False
                    break
            if deps_ok:
                runnable.append(node)
        return runnable

    def has_running_nodes(self) -> bool:
        return any(n.status == NodeStatus.RUNNING for n in self.nodes.values())

    def is_complete(self) -> bool:
        return all(n.status in [NodeStatus.SUCCESS, NodeStatus.FAILED, NodeStatus.ROLLED_BACK] for n in self.nodes.values())

    def is_success(self) -> bool:
        return all(n.status == NodeStatus.SUCCESS for n in self.nodes.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": self.edges,
            "is_success": self.is_success()
        }
