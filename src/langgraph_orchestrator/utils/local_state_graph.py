"""Lightweight fallback implementation of LangGraph's StateGraph.

This fallback enables local execution and unit testing when the real
`langgraph` dependency is not installed. It provides a minimal subset of the
StateGraph API used by the modernization scaffold.
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, Iterable, List

START = "__start__"
END = "__end__"


class StateGraph:
    """Tiny sequential state graph suitable for tests."""

    def __init__(self, _state_type: Any) -> None:  # signature parity
        self._nodes: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {}
        self._edges: Dict[str, List[str]] = {START: []}

    def add_node(self, name: str, func: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]) -> None:
        self._nodes[name] = func
        self._edges.setdefault(name, [])

    def add_edge(self, source: str, target: str) -> None:
        # Validate both source and target nodes exist
        if source not in self._nodes and source != START:
            raise ValueError(f"Node '{source}' not found in local state graph. Add it with add_node() first.")
        if target not in self._nodes and target != END:
            raise ValueError(f"Node '{target}' not found in local state graph. Add it with add_node() first.")
        self._edges.setdefault(source, []).append(target)

    def compile(self) -> "_CompiledStateGraph":
        return _CompiledStateGraph(self._nodes, self._edges)


class _CompiledStateGraph:
    def __init__(self, nodes: Dict[str, Callable], edges: Dict[str, List[str]]) -> None:
        self._nodes = nodes
        self._edges = edges

    async def ainvoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        state = dict(initial_state)
        queue: List[str] = list(self._edges.get(START, []))
        visited: set[str] = set()  # Cycle detection

        while queue:
            node_name = queue.pop(0)
            if node_name == END:
                continue

            # Skip if already visited (cycle detection)
            if node_name in visited:
                continue

            # Validate node exists
            if node_name not in self._nodes:
                raise KeyError(f"Node '{node_name}' not found in local state graph")

            node = self._nodes[node_name]
            update = await node(state)
            state.update(update)

            # Mark as visited after successful execution
            visited.add(node_name)

            for successor in self._edges.get(node_name, []):
                if successor not in visited and successor not in queue:
                    queue.append(successor)

        return state

