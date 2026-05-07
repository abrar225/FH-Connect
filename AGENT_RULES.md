# Agent Rules & Mandatory Procedures

This document outlines mandatory procedures for all AI assistants, coding agents, and automated tools interacting with the **FH-Connect** codebase.

## 🧠 Knowledge Graph (Graphify)

This project utilizes **Graphify** to maintain an architectural understanding of the codebase. The graph is stored in `graphify-out/`.

### 🚨 Mandatory Requirement
Whenever any assistant or AI coding agent changes the code or modifies any file in this project, it is **MANDATORY** to update the Graphify knowledge graph immediately after the change.

### How to Update
Run the following command in the project root:
```bash
# Using the project's Python environment
backend/.venv/bin/graphify update .
```
*(Note: `update` is fast and does not require an LLM API key).*

### How to Use the Graph
Before performing deep searches or answering architectural questions:
1.  **Consult the Report**: Read `graphify-out/GRAPH_REPORT.md` for a high-level overview.
2.  **Query the Graph**: Use `graphify query "<question>"` for relationship discovery.
3.  **Explain Concepts**: Use `graphify explain "<concept>"` to understand specific modules.

### Rules for Agents
- **Do NOT** scan the entire codebase manually if the graph can provide the answer.
- **Do NOT** load full files unless the graph context is insufficient.
- **Prefer** relationships, dependencies, and paths provided by the graph.
- **Cite** source files mentioned in the graph output.

---
*Failure to update the graph after code changes leads to architectural drift and reduced efficiency for subsequent agent tasks.*
