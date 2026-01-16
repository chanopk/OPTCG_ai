---
name: Agent Architect
description: Best practices for implementing LangGraph agents, defining State, and ensuring robust conversation flows.
---

# Agent Architect Skill

As an Agent Architect, you are responsible for maintaining the structural integrity and scalability of the LangGraph-based agents.

## Instructions

1.  **Node Definition**:
    *   Nodes should be pure functions where possible, taking `State` and returning a dict of updates.
    *   All nodes must be typed: `def my_node(state: AgentState) -> dict:`.

2.  **State Management**:
    *   Maintain the `AgentState` definition in a central location (e.g., `model.py` or `state.py` in the agent folder).
    *   Do not pollute the global state with temporary variables; use local scope or specific sub-keys.

3.  **Graph Construction**:
    *   Use explicit edges with `add_edge` and `add_conditional_edges`.
    *   Ensure there is always a path to `END` or a loop termination condition.
    *   **Guardrails**: Implement validator nodes (e.g., `validate_search_query`) before expensive calls.

4.  **Testing**:
    *   When creating a new flow, define a test case in `tests/` that simulates a user passing through that flow.
