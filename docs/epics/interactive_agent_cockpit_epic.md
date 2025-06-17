# Epic: Interactive Agent Cockpit

This epic describes a proposed evolution of the system from a reactive Human‑in‑the‑Loop (HITL) design to a proactive Human‑Agent Teaming (HAT) model. It consolidates the detailed change requests from the "Interactive Agent Cockpit" proposal (June 17, 2025) into a structured roadmap.

## 1. Goals

* Provide real‑time visibility into agent execution and reasoning.
* Enable the operator to steer tasks at varying levels of autonomy.
* Incorporate online feedback so the system learns from operator preferences.

## 2. Change Request Areas

### 2.1 Visualization & Situational Awareness

1. **CR‑1.1 Dynamic Execution Graph Visualization**
   - Render the agent's plan as a live node‑link graph with an interactive timeline and Gantt view.
   - Use OpenTelemetry traces as the data source. Employ GPU acceleration and progressive loading for large graphs.
2. **CR‑1.2 Uncertainty & Intent Display**
   - Encode confidence levels via color or line style and highlight the agent's most likely future path.
   - Selecting a belief node reveals the evidence chain that produced it.
3. **CR‑1.3 What‑If Simulation Mode**
   - Allow operators to fork from a checkpoint into a sandbox, modify plan parameters, and compare projected outcomes before committing changes back to the live agent.

### 2.2 Interactive Control & Steering

1. **CR‑2.1 Adjustable Autonomy Framework**
   - Implement discrete levels of autonomy—Manual, Assistive, Supervisory, Autonomous—with a UI slider to switch between them.
   - Provide global pause/resume controls.
2. **CR‑2.2 Hybrid Steering Interface**
   - Combine direct manipulation tools (drag‑and‑drop goals, risk sliders, map constraints) with a conversational command input linked to selected plan elements.

### 2.3 System Learning & Model Refinement

1. **CR‑3.1 Online RLHF Pipeline**
   - Capture multi‑modal operator feedback as preference pairs and periodically update the reward model via background training jobs.
2. **CR‑3.2 Feedback Efficiency Mechanisms**
   - Start with a pre‑trained reward model and use active preference elicitation so feedback is requested only when agent uncertainty is high.

## 3. Acceptance Criteria

* Operators can view and manipulate the execution graph in real time.
* Autonomy level adjustments and pause/resume controls work reliably.
* The RLHF pipeline learns from logged feedback without disrupting live execution.
* Online learning achieves alignment within a pre‑defined feedback budget.

## 4. Related Research

This epic draws on existing documentation for the Agent Introspection Toolkit and the roadmap toward Human‑Agent Teaming. It builds upon the HITL breakpoint design in `docs/hitl_breakpoint.md` and the introspection mechanisms described in `docs/research/2025-agent-introspection-toolkit.md`.
