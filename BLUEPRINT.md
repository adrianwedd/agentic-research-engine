# **Definitive Implementation Plan: A Change Request Framework for the Next-Generation Multi-Agent Research System**

## **Part I: Introduction and Strategic Framework**

### **1.1. Executive Summary**

This document presents the definitive implementation plan for evolving the current multi-agent research platform into a next-generation system. The primary objective is to transition from a stateful but architecturally constrained system to a truly cognitive, collaborative, and self-improving research platform. This evolution is driven by a series of foundational architectural shifts designed to overcome the critical limitations of existing paradigms, such as coordination bottlenecks, the absence of long-term learning, and a reliance on brittle, prompt-level controls.  
The strategic direction is anchored by four core architectural pillars. First, the adoption of a **hybrid, graph-based supervisor model**, inspired by frameworks like LangGraph, replaces the rigid orchestrator-worker hierarchy with a flexible, observable, and controllable workflow engine. Second, the implementation of a **multi-layered Long-Term Memory (LTM)** service provides the system with the cognitive capacity for lifelong learning, distinguishing between episodic (experiential), semantic (factual), and procedural (skill-based) memory. Third, a **structured self-correction loop**, featuring a dedicated Evaluator agent, institutionalizes a process of critique and refinement, moving beyond ineffective self-reflection to robust, architectural error handling. Finally, a **multi-faceted evaluation framework** ensures that progress is measured holistically, combining task-level benchmarking, rigorous output quality assessment, and metrics for system efficiency and robustness.  
Execution will follow a four-phased implementation roadmap. This approach is designed to manage complexity and deliver value incrementally. Phase 1 focuses on establishing the foundational orchestration engine and baseline agent capabilities. Phase 2 introduces the core cognitive functions of memory and self-correction. Phase 3 enables dynamic collaboration and system-level self-improvement via reinforcement learning. Finally, Phase 4 hardens the system for production-level reliability, efficiency, and specialization. This document provides the detailed change requests (CRs) that constitute this comprehensive plan.

### **1.2. The Implementation Framework: How to Read This Document**

This document serves as the canonical technical plan for all engineering, product, and quality assurance teams. Each change request (CR) detailed in the subsequent parts is presented in a standardized format to ensure clarity, provide justification, and guide implementation. The structure for each CR is as follows:

* **Identifier and Title:** A unique ID (e.g., P1-01) and a concise, descriptive title.  
* **Metadata:** A summary table detailing the CR's Phase, Epic, Category, Effort estimate (in points), a hint for the primary Owner team, and any direct CR Dependencies.  
* **Strategic Rationale:** A clear explanation of *why* the CR is necessary, directly linking the work item to the strategic goals, critiques, and architectural principles outlined in the 'Multi-Agent Research System Improvement' blueprint. This section provides the business and technical justification for the allocated effort.  
* **Detailed Description:** A comprehensive, formal description of the work to be performed, elaborating on the feature or capability to be implemented.  
* **Refined Acceptance Criteria:** A set of precise, verifiable conditions that must be met for the CR to be considered complete. These criteria have been systematically refined from the initial ledger to align with the best practices of Behavior-Driven Development (BDD), ensuring they are clear, testable, and focused on system behavior.  
* **Implementation Notes:** Expert-level guidance, technical considerations, and specific recommendations for the engineering teams responsible for implementation. This may include suggestions for specific libraries, architectural patterns, or potential pitfalls to avoid.

A core principle of the target architecture is the move away from brittle, prompt-based fixes toward robust, systemic solutions. This philosophy is mirrored in the very structure of this plan. The acceptance criteria are written in a declarative style, describing *what* the system does, not *how* it does it. This BDD approach, which favors describing behavior over implementation details, aligns our development and testing methodology with the architectural principles of the system being built. Just as the system's architecture is designed for robustness, the development process defined here is structured to produce robust, well-tested software. This document, therefore, does not merely list tasks; it embodies the project's core philosophy in its structure, providing a coherent and rigorous framework for execution.

### **1.3. Phased Execution and Dependency Overview**

The four-phase plan provides a logical, incremental path to realizing the full vision of the next-generation system. This staged approach de-risks the project by ensuring that foundational components are built and stabilized before more complex capabilities are added.

* **Phase 1: Core Orchestration and Foundational Capabilities.** This phase focuses on laying the essential groundwork. It involves building the system's skeleton: the graph-based orchestration engine, the observability layer, the secure tool registry, and a set of initial agents and QA benchmarks. The goal is to produce a functional, testable system that serves as the platform for all future enhancements.  
* **Phase 2: Advanced Cognition and Evaluation.** With the foundation in place, this phase builds the "mind" of the system. It introduces the Long-Term Memory service, enabling the system to learn from experience, and the Evaluator agent with its self-correction loop, enabling it to identify and fix its own errors. This phase also builds out the sophisticated LLM-as-a-Judge evaluation pipeline.  
* **Phase 3: Dynamic Collaboration and Self-Improvement.** This phase transforms the system from a collection of individual workers into a collaborative collective. It introduces mechanisms for agent teaming and peer-to-peer communication. Critically, it implements the RLAIF (Reinforcement Learning from AI Feedback) loop, allowing the system to learn from its own performance and improve its strategies over time.  
* **Phase 4: Production Hardening and Specialization.** The final phase prepares the system for production deployment. It focuses on performance tuning, enhancing agent skills through procedural memory, fostering agent specialization via multi-agent fine-tuning, and implementing robust production-hardening features like state checkpointing and comprehensive failure-mode testing.

The system we are building is fundamentally a graph, managing the flow of state and control between agentic nodes. Similarly, the project plan to build it is a complex graph of dependencies between tasks. A linear document struggles to represent this interconnectedness. To aid in project management, it is strongly recommended that the dependency data within this plan be used to generate a visual dependency graph. Tools such as Graphviz or Tach can be employed to create a clear visualization of the project's critical path, potential bottlenecks, and task relationships. This provides the project management and leadership teams with a powerful, at-a-glance tool for resource planning and risk assessment, applying the system's core architectural principle to its own development lifecycle.

#### **Table 1: Master Change Request Ledger Summary**

| ID | Title | Phase | Epic | Category | Effort | Dependencies | Owner Hint |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| P1-01 | Set up mono-repo for agentic system | 1 | Scaffolding | Infra | 3 pts | None | Ops |
| P1-02 | Implement CI pipeline for automated builds and tests | 1 | Scaffolding | Infra | 5 pts | P1-01 | Ops |
| P1-03 | Implement CD Pipeline for automated deployments | 1 | Scaffolding | Infra | 5 pts | P1-02 | Ops |
| P1-04 | Set up OpenTelemetry collector and exporter | 1 | Scaffolding | Infra | 3 pts | None | Ops |
| P1-05 | Define core agent action tracing schema | 1 | Observability | Feature | 2 pts | P1-04 | BE |
| P1-06 | Implement core Orchestration Engine with graph execution | 1 | Orchestration | Feature | 8 pts | None | BE |
| P1-07 | Define and implement the central State object | 1 | Orchestration | Feature | 3 pts | P1-06 | BE |
| P1-08 | Implement conditional edge router for dynamic workflows | 1 | Orchestration | Feature | 5 pts | P1-07 | BE |
| P1-09 | Implement Supervisor agent for query analysis | 1 | Core Agents | Feature | 3 pts | P1-06 | ML |
| P1-10 | Implement Supervisor's graph-based planning logic | 1 | Core Agents | Feature | 5 pts | P1-09 | ML |
| P1-11 | Implement WebResearcher agent for information extraction | 1 | Core Agents | Feature | 3 pts | P1-14 | ML |
| P1-12 | Implement WebResearcher's summarization capability | 1 | Core Agents | Feature | 3 pts | P1-11 | ML |
| P1-13 | Create secure Tool Registry service | 1 | Core Agents | Infra | 5 pts | None | BE |
| P1-14 | Implement Web Search tool wrapper | 1 | Core Agents | Feature | 2 pts | P1-13 | BE |
| P1-15 | Implement PDF Reader tool wrapper | 1 | Core Agents | Feature | 3 pts | P1-13 | BE |
| P1-16 | Implement HTML Scraper tool wrapper | 1 | Core Agents | Feature | 2 pts | P1-13 | BE |
| P1-17 | Create initial BrowseComp benchmark dataset | 1 | Foundational QA | QA | 5 pts | None | PM |
| P1-18 | Implement Integration-Test Harness for benchmarks | 1 | Foundational QA | QA | 8 pts | P1-06, P1-17 | QA |
| P1-19 | Create basic unit test framework and coverage goals | 1 | Foundational QA | QA | 2 pts | P1-01 | QA |
| P1-20 | Research optimal graph compilation strategies | 1 | Orchestration | Research | 3 pts | P1-06 | ML |
| P2-01 | Implement LTM Service API for memory operations | 2 | Long-Term Memory | Feature | 5 pts | P1-13 | BE |
| P2-02 | Integrate vector database for Episodic Memory | 2 | Long-Term Memory | Infra | 5 pts | P2-01 | Ops |
| P2-03 | Implement MemoryManager agent for episodic consolidation | 2 | Long-Term Memory | Feature | 5 pts | P2-01 | ML |
| P2-04 | Enhance Supervisor to query Episodic LTM for plan templating | 2 | Long-Term Memory | Feature | 5 pts | P2-01, P1-10 | ML |
| P2-05 | Implement Evaluator agent for critique generation | 2 | Self-Correction | Feature | 3 pts | P1-06 | ML |
| P2-06 | Implement Evaluator's factual accuracy verification logic | 2 | Self-Correction | Feature | 5 pts | P2-05, P2-09 | ML |
| P2-07 | Implement Evaluator's source quality assessment logic | 2 | Self-Correction | Feature | 3 pts | P2-05 | ML |
| P2-08 | Modify Orchestration Engine to support CoSC feedback loop | 2 | Self-Correction | Feature | 8 pts | P1-08, P2-05 | BE |
| P2-09 | Integrate a fact-checking API as an Evaluator tool | 2 | Self-Correction | Feature | 3 pts | P1-13, P2-05 | BE |
| P2-10 | Develop QA tests for the CoSC loop to prevent infinite cycles | 2 | Self-Correction | QA | 3 pts | P2-08 | QA |
| P2-11 | Build LLM-as-a-Judge evaluation pipeline | 2 | Evaluation Framework | Infra | 8 pts | P1-18 | Ops |
| P2-12 | Define comprehensive evaluation rubric as a JSON schema | 2 | Evaluation Framework | Feature | 3 pts | P2-11 | PM |
| P2-13 | Curate and label golden dataset of reports for judge calibration | 2 | Evaluation Framework | QA | 8 pts | P2-11 | PM |
| P2-14 | Implement judge calibration test suite against golden dataset | 2 | Evaluation Framework | QA | 5 pts | P2-11, P2-13 | QA |
| P2-15 | Research synthetic data generation techniques for self-correction | 2 | Self-Correction | Research | 5 pts | None | ML |
| P2-16 | Create synthetic dataset of errors and corrections | 2 | Self-Correction | ML | 5 pts | P2-15 | ML |
| P2-17 | Fine-tune Evaluator agent on the correction dataset | 2 | Self-Correction | ML | 8 pts | P2-16 | ML |
| P2-18 | Implement a human-in-the-loop breakpoint | 2 | Orchestration | Feature | 5 pts | P1-06 | UX |
| P2-19 | Research memory consolidation and forgetting strategies | 2 | Long-Term Memory | Research | 5 pts | P2-01 | ML |
| P2-20 | Implement basic LTM forgetting mechanism | 2 | Long-Term Memory | Feature | 3 pts | P2-01, P2-19 | BE |
| P3-01 | Implement GroupChatManager for agent collaboration | 3 | Collaboration | Feature | 8 pts | P1-06 | BE |
| P3-02 | Define agent message passing protocol for group chat | 3 | Collaboration | Feature | 3 pts | P3-01 | BE |
| P3-03 | Implement hierarchical subgraph spawning for agent teams | 3 | Collaboration | Feature | 8 pts | P1-10 | BE |
| P3-04 | Implement a shared collaborative scratchpad | 3 | Collaboration | Feature | 3 pts | P1-07, P3-01 | BE |
| P3-05 | Develop QA tests for inter-agent communication protocols | 3 | Collaboration | QA | 5 pts | P3-02 | QA |
| P3-06 | Implement Reward Model training pipeline | 3 | Self-Improvement | ML | 13 pts | P2-11 | ML |
| P3-07 | Integrate a PPO library for RLAIF loop | 3 | Self-Improvement | ML | 8 pts | P3-06 | ML |
| P3-08 | Connect RLAIF loop to update Supervisor's policy | 3 | Self-Improvement | ML | 5 pts | P3-07, P1-10 | ML |
| P3-09 | Log system and collaboration metrics for the Reward Model | 3 | Self-Improvement | Infra | 3 pts | P1-05, P3-06 | BE |
| P3-10 | Research SCoRe-based reward shaping for self-correction | 3 | Self-Improvement | Research | 5 pts | P3-06 | ML |
| P3-11 | Implement CodeResearcher agent with secure tool use | 3 | Core Agents | Feature | 5 pts | P3-12, P3-18 | ML |
| P3-12 | Provision secure code interpreter sandbox environment | 3 | Core Agents | Infra | 8 pts | None | Ops |
| P3-13 | Implement Planner agent base class | 3 | Core Agents | Feature | 3 pts | P1-06 | ML |
| P3-14 | Implement greedy algorithm for task allocation in Planner | 3 | Core Agents | Feature | 5 pts | P3-13 | ML |
| P3-15 | Integrate graph database for Semantic LTM | 3 | Long-Term Memory | Infra | 5 pts | P2-01 | Ops |
| P3-16 | Enhance MemoryManager to extract entities for knowledge graph | 3 | Long-Term Memory | Feature | 8 pts | P2-03, P3-15 | ML |
| P3-17 | Implement agent query path for Semantic LTM | 3 | Long-Term Memory | Feature | 3 pts | P3-15 | BE |
| P3-18 | Implement a basic Code Interpreter tool | 3 | Core Agents | Feature | 5 pts | P1-13, P3-12 | BE |
| P3-19 | Implement a GitHub Search API tool | 3 | Core Agents | Feature | 2 pts | P1-13 | BE |
| P3-20 | Research emergent communication protocols in group chat | 3 | Collaboration | Research | 8 pts | P3-01 | ML |
| P3-21 | Develop QA tests for race conditions in group chat | 3 | Collaboration | QA | 5 pts | P3-01 | QA |
| P4-01 | Implement Procedural Memory module in LTM Service | 4 | Performance Tuning | Feature | 5 pts | P2-01 | BE |
| P4-02 | Instrument agents to identify and store successful tool sequences | 4 | Performance Tuning | Feature | 5 pts | P4-01 | ML |
| P4-03 | Enhance agents to query and execute stored procedures | 4 | Performance Tuning | Feature | 5 pts | P4-01 | ML |
| P4-04 | Add LTM hit-rate metrics to observability dashboard | 4 | Performance Tuning | Infra | 3 pts | P1-04, P2-01 | FE |
| P4-05 | Research RAG vs fine-tuning for procedural memory recall | 4 | Performance Tuning | Research | 5 pts | P4-01 | ML |
| P4-06 | Build MLOps pipeline for parallel multi-agent fine-tuning | 4 | Agent Specialization | ML | 13 pts | P3-08 | Ops |
| P4-07 | Modify Supervisor to select agents from a diverse, specialized pool | 4 | Agent Specialization | Feature | 5 pts | P4-06 | ML |
| P4-08 | Develop agent policy divergence and specialization metrics | 4 | Agent Specialization | QA | 3 pts | P4-06 | QA |
| P4-09 | Implement CitationAgent with source-claim matching logic | 4 | Production Hardening | Feature | 8 pts | None | ML |
| P4-10 | Implement citation formatting based on specified styles | 4 | Production Hardening | Feature | 3 pts | P4-09 | BE |
| P4-11 | Integrate CitationAgent as a final, mandatory graph node | 4 | Production Hardening | Feature | 3 pts | P1-10, P4-09 | BE |
| P4-12 | Implement state checkpointing for robust fault recovery | 4 | Production Hardening | Infra | 5 pts | P1-07 | BE |
| P4-13 | Implement exponential backoff and retry logic in tool calls | 4 | Production Hardening | Feature | 3 pts | P1-13 | BE |
| P4-14 | Develop MAST test for Step Repetition (FM-1.3) | 4 | Production Hardening | QA | 3 pts | P1-18, P2-04 | QA |
| P4-15 | Develop MAST test for Information Withholding (FM-2.4) | 4 | Production Hardening | QA | 5 pts | P1-18, P3-01 | QA |
| P4-16 | Develop MAST test for Incorrect Verification (FM-3.3) | 4 | Production Hardening | QA | 5 pts | P1-18, P2-06 | QA |
| P4-17 | Expand Tool Registry with specialized database connectors | 4 | Production Hardening | Feature | 5 pts | P1-13 | BE |
| P4-18 | Research spatio-temporal memory structures | 4 | Long-Term Memory | Research | 8 pts | P2-01 | ML |

## **Part II: Phase 1 \- Core Orchestration and Foundational Capabilities**

This part details the change requests required to build the system's skeleton: a functional, observable, and testable graph-based orchestration platform with basic agent capabilities. The successful completion of this phase will yield a robust foundation upon which all advanced cognitive and collaborative features will be built.

### **2.1. Epic: Scaffolding**

This epic establishes the professional-grade infrastructure for development, deployment, and observability. It directly addresses the "Debugging and Deployment Complexity" and "Statefulness and Error Propagation" limitations identified in the technical blueprint by implementing industry-standard MLOps and DevOps practices from the outset.

#### **P1-01 – Set up mono-repo for agentic system**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Scaffolding |
| **Category** | Infra |
| **Effort** | 3 pts |
| **Owner Hint** | Ops |
| **Dependencies** | None |

**Strategic Rationale** The technical blueprint identifies "Debugging and Deployment Complexity" as a critical limitation of existing agentic systems. This change request directly addresses this challenge at its root by establishing a unified version control system. A mono-repo architecture centralizes all system artifacts—agent code, infrastructure-as-code definitions, and ML model configurations—providing a single source of truth and simplifying dependency management, which is crucial for a complex, multi-component system.  
**Detailed Description** This task involves the creation of a new Git mono-repository to house all source code and related artifacts for the multi-agent system. The repository must be configured with modern governance and quality control mechanisms, including branch protection rules to safeguard critical branches (e.g., main, staging) and pre-commit hooks to enforce code quality standards automatically before code is even committed.  
**Refined Acceptance Criteria**  
`Feature: Mono-repo setup and governance`

  `Scenario: Enforce branch protection rules`  
    `Given a developer has cloned the repository`  
    `And a branch is protected with a required review rule`  
    `When the developer attempts to push a commit directly to the protected branch`  
    `Then the push is rejected by the version control system`

  `Scenario: Enforce code quality with pre-commit hooks`  
    `Given a developer has staged changes containing linting errors`  
    `When the developer attempts to create a commit`  
    `Then the pre-commit hook fails and prevents the commit`

**Implementation Notes**

* **Branch Protection:** Configure rules in the version control system (e.g., GitHub, GitLab) to require at least one peer review and successful completion of CI status checks (P1-02) before a pull request can be merged into the main branch.  
* **Pre-commit Hooks:** Use a framework like pre-commit to manage hooks. Recommended hooks include black for standardized code formatting, flake8 or ruff for linting, and isort for organizing imports.

#### **P1-02 – Implement CI pipeline for automated builds and tests**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Scaffolding |
| **Category** | Infra |
| **Effort** | 5 pts |
| **Owner Hint** | Ops |
| **Dependencies** | P1-01 |

**Strategic Rationale** Continuous Integration (CI) is a foundational practice for mitigating the risk of "Statefulness and Error Propagation" identified in the blueprint. By automatically building and testing every proposed change, the CI pipeline acts as the first line of defense against regressions and ensures a baseline level of code quality, preventing faulty code from being integrated into the main branch.  
**Detailed Description** Implement a CI pipeline using a standard platform (e.g., GitHub Actions, Jenkins, CircleCI) that triggers automatically on the creation of pull requests. This pipeline is responsible for building all services within the mono-repo, running static analysis tools (linters), and executing the complete suite of unit tests (P1-19). The final status of the pipeline (pass/fail) must be reported back to the version control system as a status check on the pull request.  
**Refined Acceptance Criteria**  
`Feature: Continuous Integration Pipeline`

  `Scenario: Successful PR validation`  
    `Given a pull request is opened with valid code changes`  
    `When the CI pipeline completes successfully`  
    `Then a "pass" status check is visible on the pull request`

  `Scenario: Failed PR validation due to test failure`  
    `Given a pull request is opened with code changes that break a unit test`  
    `When the CI pipeline runs the test suite`  
    `Then the pipeline run is marked as "failed"`  
    `And a "fail" status check is visible on the pull request`

**Implementation Notes**

* The pipeline should be optimized for speed by caching dependencies and running jobs in parallel where possible.  
* The CI configuration file (e.g., workflow.yml) must reside within the mono-repo itself, versioning the pipeline alongside the code it tests.

#### **P1-03 – Implement CD Pipeline for automated deployments**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Scaffolding |
| **Category** | Infra |
| **Effort** | 5 pts |
| **Owner Hint** | Ops |
| **Dependencies** | P1-02 |

**Strategic Rationale** Automated deployment is essential for managing the complexity of a multi-service agentic system. The blueprint explicitly notes the need for careful deployment strategies to avoid disrupting long-running agents. This Continuous Deployment (CD) pipeline automates the release process, reducing manual error and enabling advanced strategies like rainbow deployments to ensure system availability.  
**Detailed Description** Implement a CD pipeline that automates the deployment of all system services. The pipeline should trigger automatically upon a successful merge to the main branch, deploying the new version to a staging environment for verification. The promotion of a version from staging to the production environment must be a manual, gated step, requiring explicit operator approval.  
**Refined Acceptance Criteria**  
`Feature: Continuous Deployment Pipeline`

  `Scenario: Automated deployment to staging`  
    `Given a pull request has been successfully merged into the main branch`  
    `When the CD pipeline is triggered`  
    `Then all system services are automatically deployed to the staging environment`

  `Scenario: Manual promotion to production`  
    `Given the staging deployment has been verified and approved`  
    `When an operator triggers the "promote-to-production" step`  
    `Then the version from staging is deployed to the production environment`

**Implementation Notes**

* The pipeline must be designed to support zero-downtime deployment strategies. The blueprint specifically mentions "rainbow deployments," which involve deploying the new version alongside the old one and gradually shifting traffic. This is critical for long-running agent processes that cannot be abruptly terminated.  
* All deployment configurations should be managed via infrastructure-as-code (e.g., Terraform, Helm charts) stored within the mono-repo.

#### **P1-04 – Set up OpenTelemetry collector and exporter**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Scaffolding |
| **Category** | Infra |
| **Effort** | 3 pts |
| **Owner Hint** | Ops |
| **Dependencies** | None |

**Strategic Rationale** The blueprint identifies "full production tracing" as a non-negotiable requirement for debugging and evaluating non-deterministic agentic systems. This CR establishes the foundational infrastructure for the "Observability & Evaluation Layer" by deploying an OpenTelemetry collector, the industry standard for collecting logs, metrics, and traces.  
**Detailed Description** This task involves deploying and configuring an OpenTelemetry (OTel) collector within the system's infrastructure. The collector will be configured to receive telemetry data from all system components (agents, services, orchestration engine), process it, and export it to a configured observability backend (e.g., Jaeger, Datadog, Honeycomb) for storage and analysis.  
**Refined Acceptance Criteria**  
`Feature: Observability Data Collection`

  `Scenario: A trace is successfully collected and exported`  
    `Given the OpenTelemetry collector is running`  
    `And a system service is instrumented to send traces`  
    `When the service performs an action and emits a trace`  
    `Then the corresponding trace is visible in the configured observability backend`

**Implementation Notes**

* The collector should be deployed as a highly available service.  
* Configuration should include processors for batching data to improve efficiency and adding metadata (e.g., environment, service version) to all telemetry signals.

### **2.2. Epic: Observability**

This epic builds upon the scaffolding by defining the *content* of the telemetry data, ensuring that the collected traces are not just present, but also structured, meaningful, and useful for downstream processes.

#### **P1-05 – Define core agent action tracing schema**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Observability |
| **Category** | Feature |
| **Effort** | 2 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-04 |

**Strategic Rationale** This CR is a direct implementation of a key component of the "Observability & Evaluation Layer". Raw traces are insufficient; a standardized schema is required to make observability data queryable and useful for automated analysis. This schema provides the structured data necessary for advanced debugging, the evaluation framework (P2-11), and the RLAIF loop (P3-06), which relies on analyzing execution traces.  
**Detailed Description** Define and document a standardized OpenTelemetry tracing schema that will be used across the entire system. This schema must specify the attributes (metadata) to be included in trace spans for key agent actions, such as tool calls, inter-agent messages, and significant state changes. This ensures consistency and allows for powerful, targeted queries on the observability data.  
**Refined Acceptance Criteria**  
`Feature: Standardized Agent Tracing`

  `Scenario: An agent tool call is traced according to the schema`  
    `Given the agent action tracing schema is defined`  
    `When a 'WebResearcher' agent calls the 'web_search' tool with a query`  
    `Then a trace span is emitted containing attributes for 'agent_id', 'agent_role', 'tool_name', 'tool_input', and 'tool_output'`

**Implementation Notes**

* The schema should be defined in a shared library or document accessible to all development teams.  
* The schema should be versioned to allow for future evolution without breaking existing instrumentation.  
* Consider including metrics like token counts (input\_tokens, output\_tokens) and latency for each LLM call within the trace attributes.

### **2.3. Epic: Orchestration**

This epic implements the core of the new architecture, replacing the rigid, centralized orchestrator of the baseline system with a flexible, stateful, and dynamic graph-based engine. This directly addresses the "synchronous execution bottlenecks" and lack of adaptability critiqued in the blueprint.

#### **P1-06 – Implement core Orchestration Engine with graph execution**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Orchestration |
| **Category** | Feature |
| **Effort** | 8 pts |
| **Owner Hint** | BE |
| **Dependencies** | None |

**Strategic Rationale** This CR is the cornerstone of the "Hybrid Graph-Based Supervisor Model". It replaces the inflexible orchestrator-worker paradigm with a dynamic graph architecture, as advocated by the blueprint. This shift from centralized control to a stateful graph execution model is the primary mechanism for enabling complex, non-linear workflows and overcoming the architectural limitations of the baseline system.  
**Detailed Description** Implement the core orchestration engine, taking inspiration from the LangGraph framework. The engine must provide functionalities to define a workflow as a graph of nodes (agents) and edges (transitions). It must be able to compile this graph definition and execute it, managing the flow of control and passing state between the nodes according to the graph's structure.  
**Refined Acceptance Criteria**  
`Feature: Graph-based Workflow Execution`

  `Scenario: Execute a simple sequential graph`  
    `Given a graph is defined with NodeA followed by NodeB`  
    `When the Orchestration Engine's 'execute' method is called with this graph`  
    `Then NodeA is executed to completion before NodeB is executed`

**Implementation Notes**

* The blueprint explicitly cites LangGraph as an inspiration. It is highly recommended to use LangGraph as the reference implementation or directly as the underlying library to accelerate development.  
* The engine must be instrumented to emit OpenTelemetry traces (P1-04, P1-05) for every node execution and edge transition, providing deep visibility into the workflow.  
* The engine should expose a method to export the graph structure in a standard format (e.g., DOT), which can be used by tools like Graphviz for visualization and debugging.

#### **P1-07 – Define and implement the central State object**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Orchestration |
| **Category** | Feature |
| **Effort** | 3 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-06 |

**Strategic Rationale** A graph-based architecture requires a mechanism for sharing information between nodes. The central State object serves this purpose, acting as the "single source of truth" for a given research task. This decouples state from the agents themselves, a key principle of the LangGraph model, and is the prerequisite for robust state management, error recovery (P4-12), and human-in-the-loop interventions (P2-18).  
**Detailed Description** Define and implement a data structure, referred to as the State object, which will be passed between all nodes in the execution graph. This object must be designed to hold all information relevant to a research task, including the initial query, the evolving plan, a list of agent messages, tool outputs, and any other metadata. A critical requirement is that the object must be serializable to allow for persistent checkpointing.  
**Refined Acceptance Criteria**  
`Feature: Centralized State Management`

  `Scenario: State is passed between nodes`  
    `Given a graph where NodeA modifies the 'State' object`  
    `When the graph is executed`  
    `Then the modified 'State' object is passed as input to the subsequent node`

  `Scenario: State object is serializable`  
    `Given a 'State' object containing data`  
    `When the object is serialized and then deserialized`  
    `Then the resulting object is identical to the original`

**Implementation Notes**

* Use a library like Pydantic in Python to define the State object's schema, which provides data validation and serialization capabilities out of the box.  
* The State object should be designed to be append-only where possible (e.g., for lists of messages) to provide a clear audit trail of how the state evolved over time.

#### **P1-08 – Implement conditional edge router for dynamic workflows**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Orchestration |
| **Category** | Feature |
| **Effort** | 5 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-07 |

**Strategic Rationale** Conditional edges are what make the graph architecture truly dynamic and adaptive. This capability allows the workflow to change its path based on the results of previous steps, which is essential for complex research tasks where the optimal path is not known in advance. This feature directly enables the implementation of the self-correction loop (P2-08) and other adaptive behaviors.  
**Detailed Description** Implement logic within the Orchestration Engine to support conditional edges. A conditional edge is a function that is executed after a node completes. This function inspects the central State object and returns the name of the next node to execute. This allows the graph to branch and route execution dynamically based on the data and outcomes generated during the workflow.  
**Refined Acceptance Criteria**  
`Feature: Dynamic Workflow Routing`

  `Scenario: Route to verification node based on state`  
    `Given a graph is defined with a conditional edge routing on the 'status' field`  
    `And the central State object has 'status' set to 'requires_verification'`  
    `When the Orchestration Engine executes the current node`  
    `Then the next node to be executed is the 'Verifier' node`

**Implementation Notes**

* The router function should be simple and deterministic, containing only the logic to inspect the state and return a string identifier for the next node. All complex business logic should remain within the agent nodes themselves.

#### **P1-20 – Research optimal graph compilation strategies**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Orchestration |
| **Category** | Research |
| **Effort** | 3 pts |
| **Owner Hint** | ML |
| **Dependencies** | P1-06 |

**Strategic Rationale** While a dynamic, just-in-time execution model offers maximum flexibility, it may not be the most performant or efficient for all use cases. This research task ensures that the architectural choice for graph compilation is a deliberate one, based on a clear understanding of the trade-offs between flexibility, performance, and debuggability.  
**Detailed Description** This task is a research spike to investigate and compare different strategies for compiling the agent graph into an executable format. The research should analyze the pros and cons of dynamic, just-in-time (JIT) compilation (where the graph is interpreted at runtime) versus static, ahead-of-time (AOT) compilation (where the graph is compiled into a more optimized, static workflow before execution).  
**Refined Acceptance Criteria**  
`Feature: Graph Compilation Strategy`

  `Scenario: Deliver research findings`  
    `Given research has been conducted on graph compilation strategies`  
    `When a final report is delivered to technical leadership`  
    `Then the report contains a clear recommendation for the chosen strategy, supported by performance benchmarks and qualitative analysis`

**Implementation Notes**

* The research should include small-scale proof-of-concept implementations to gather empirical data on latency and resource usage for both approaches.  
* The final recommendation may be a hybrid approach, where certain well-defined subgraphs can be compiled AOT for performance, while the main orchestrating graph remains dynamic.

### **2.4. Epic: Core Agents**

This epic creates the initial set of agents that will operate within the new orchestration framework. It implements the Supervisor agent, the system's primary strategist, and the WebResearcher agent, its primary information gatherer, along with the secure tooling they require.

#### **P1-09 – Implement Supervisor agent for query analysis**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Core Agents |
| **Category** | Feature |
| **Effort** | 3 pts |
| **Owner Hint** | ML |
| **Dependencies** | P1-06 |

**Strategic Rationale** The Supervisor agent is the evolution of the LeadResearcher from the baseline system. This CR implements its most basic function: acting as the primary entry point for the system. It ingests the user's request and initializes the workflow by creating the initial State object.  
**Detailed Description** Implement the initial version of the Supervisor agent. This version's responsibility is to receive a user query as a string, perform a basic analysis, and create and populate the initial State object (P1-07) that will be used to kick off the execution of the research graph.  
**Refined Acceptance Criteria**  
`Feature: Supervisor Agent Query Ingestion`

  `Scenario: Initialize state from user query`  
    `Given the Supervisor agent is invoked with a user query string`  
    `When the agent completes its analysis`  
    `Then it returns a 'State' object with the original query populated in the 'initial_query' field`

**Implementation Notes**

* The Supervisor agent will be implemented as a node within the orchestration graph (P1-06). It will typically be the entry point of the graph.

#### **P1-10 – Implement Supervisor's graph-based planning logic**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Core Agents |
| **Category** | Feature |
| **Effort** | 5 pts |
| **Owner Hint** | ML |
| **Dependencies** | P1-09 |

**Strategic Rationale** This CR implements the most critical new capability of the Supervisor: the ability to generate a graph-based plan. This is a fundamental departure from the baseline system's linear planning and is the key enabler for the flexible, parallel, and dynamic workflows of the new architecture.  
**Detailed Description** Enhance the Supervisor agent with the logic to decompose a complex user query into a high-level research plan. Crucially, the agent must not output a simple list of steps. Instead, it must generate a formal graph definition (a collection of nodes and edges) that can be compiled and executed by the Orchestration Engine (P1-06).  
**Refined Acceptance Criteria**  
`Feature: Supervisor Agent Graph-Based Planning`

  `Scenario: Generate a parallel research plan`  
    `Given the Supervisor agent receives a query like "Compare the performance of Transformer and LSTM models"`  
    `When the agent generates a research plan`  
    `Then the output graph definition contains at least two parallel 'WebResearcher' nodes, one for 'Transformer performance' and one for 'LSTM performance'`

**Implementation Notes**

* The prompt for the Supervisor agent must be carefully engineered to instruct the LLM to output the plan in the specific JSON or YAML format that the Orchestration Engine expects for graph definitions.

#### **P1-11 – Implement WebResearcher agent for information extraction**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Core Agents |
| **Category** | Feature |
| **Effort** | 3 pts |
| **Owner Hint** | ML |
| **Dependencies** | P1-14 |

**Strategic Rationale** The WebResearcher agent is the primary "worker" in the initial system, analogous to the Subagent in the baseline model. It is responsible for executing the information-gathering sub-tasks defined in the Supervisor's plan.  
**Detailed Description** Implement the WebResearcher agent as a callable node in the execution graph. The agent will be designed to receive a specific research sub-task from the State object. Its core function is to use the Web Search tool (P1-14) to find relevant information on the internet and then write the extracted content back into the central State object for use by other agents.  
**Refined Acceptance Criteria**  
`Feature: WebResearcher Agent Information Gathering`

  `Scenario: Execute a research sub-task`  
    `Given the 'State' object contains a sub-task for the WebResearcher to "find papers on Transformer architecture"`  
    `When the 'WebResearcher' node is executed`  
    `Then the agent calls the 'web_search' tool with a relevant query, such as "Transformer architecture academic papers"`

**Implementation Notes**

* The agent's internal logic should employ reasoning techniques like those described in the blueprint (e.g., "interleaved thinking") to analyze search results and decide which links to follow and scrape.

#### **P1-12 – Implement WebResearcher's summarization capability**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Core Agents |
| **Category** | Feature |
| **Effort** | 3 pts |
| **Owner Hint** | ML |
| **Dependencies** | P1-11 |

**Strategic Rationale** A key function of worker agents is to act as "intelligent filters," compressing large amounts of information into concise summaries. This summarization capability prevents downstream agents (like the Supervisor) from being overwhelmed by raw text and reduces the token count passed between steps, improving efficiency.  
**Detailed Description** Add a summarization capability to the WebResearcher agent. After using tools like the HTML Scraper (P1-16) or PDF Reader (P1-15) to extract large volumes of raw text, the agent must use an LLM call to condense this text into a concise, relevant summary. This summary is then written to the messages list in the State object.  
**Refined Acceptance Criteria**  
`Feature: WebResearcher Agent Summarization`

  `Scenario: Condense raw text into a summary`  
    `Given the WebResearcher agent has extracted 5,000 words of raw text from a webpage`  
    `When the agent completes its turn`  
    `Then a concise summary of that text is added to the 'messages' list in the 'State' object`

**Implementation Notes**

* The summarization prompt should instruct the agent to focus on extracting information that is directly relevant to the sub-task it was assigned.

#### **P1-13 – Create secure Tool Registry service**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Core Agents |
| **Category** | Infra |
| **Effort** | 5 pts |
| **Owner Hint** | BE |
| **Dependencies** | None |

**Strategic Rationale** The blueprint highlights the baseline system's use of a formal "agent-tool interface" as a sound design principle. This CR implements an improved version of that concept: a centralized, secure Tool Registry. By adding versioning and role-based access control (RBAC), the registry enhances security and manageability, ensuring agents can only use tools they are authorized for.  
**Detailed Description** Create a centralized, standalone service for managing all external tools. This Tool Registry will be responsible for defining, versioning, and providing access to tools like web search or a code interpreter. Agents must request access to a tool from the registry. The registry will enforce access control policies, returning a callable interface for authorized requests and an error for unauthorized ones.  
**Refined Acceptance Criteria**  
`Feature: Secure Tool Access Control`

  `Scenario: Agent requests an authorized tool`  
    `Given the 'WebResearcher' agent has permission to use the 'web_search' tool`  
    `When the agent requests the 'web_search' tool from the registry`  
    `Then the registry returns a callable interface for the tool`

  `Scenario: Agent requests an unauthorized tool`  
    `Given the 'WebResearcher' agent does NOT have permission to use the 'code_interpreter' tool`  
    `When the agent requests the 'code_interpreter' tool from the registry`  
    `Then the registry returns an 'AccessDeniedError'`

**Implementation Notes**

* The registry should expose a simple, stable API (e.g., REST or gRPC) for agents to query.  
* Tool permissions can be defined in a configuration file or a database, mapping agent roles to permitted tool names.

#### **P1-14 – Implement Web Search tool wrapper**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Core Agents |
| **Category** | Feature |
| **Effort** | 2 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-13 |

**Strategic Rationale** This CR provides the most fundamental tool for any research agent: the ability to search the web. This is a core capability of the baseline system that must be replicated.  
**Detailed Description** Create a Web Search tool and register it with the Tool Registry (P1-13). This tool will act as a wrapper around a commercial search API (e.g., Google Search API, Bing Web Search API, Serper API). The wrapper must handle all aspects of interacting with the external API, including authentication (API keys), query formatting, and parsing the JSON response into a standardized list of search result objects for agent consumption.  
**Refined Acceptance Criteria**  
`Feature: Web Search Tool`

  `Scenario: Perform a web search`  
    `Given the Web Search tool is called with the query string "multi-agent systems"`  
    `When the tool successfully communicates with the external API`  
    `Then it returns a list of search result objects, where each object contains a 'url', 'title', and 'snippet'`

**Implementation Notes**

* API keys and other secrets must be managed securely (e.g., via a secret manager like AWS Secrets Manager or HashiCorp Vault) and not hardcoded in the tool's source code.

#### **P1-15 – Implement PDF Reader tool wrapper**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Core Agents |
| **Category** | Feature |
| **Effort** | 3 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-13 |

**Strategic Rationale** Much of the high-quality information required for serious research is contained in PDF documents, such as academic papers and official reports. This tool is essential for enabling agents to access and reason about this critical source of knowledge.  
**Detailed Description** Create a PDF Reader tool and register it with the Tool Registry (P1-13). The tool will accept a URL or a local file path to a PDF document. It must be ableto download (if necessary) and parse the document to extract the full, raw text content, which is then returned as a single string.  
**Refined Acceptance Criteria**  
`Feature: PDF Reader Tool`

  `Scenario: Extract text from a PDF document`  
    `Given the PDF Reader tool is called with a URL to a valid, text-based PDF document`  
    `When the tool successfully downloads and parses the document`  
    `Then it returns a string containing the full text content of the document`

**Implementation Notes**

* Use a robust Python library like PyMuPDF or pdfplumber for reliable text extraction.  
* The tool should include error handling for non-existent files, invalid URLs, and scanned (image-based) PDFs that do not contain extractable text.

#### **P1-16 – Implement HTML Scraper tool wrapper**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Core Agents |
| **Category** | Feature |
| **Effort** | 2 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-13 |

**Strategic Rationale** Raw HTML from web pages contains a significant amount of "noise" (ads, navigation bars, footers) that can confuse LLMs and consume valuable context window space. This tool provides agents with cleaner, more relevant text, improving the quality of their reasoning and summarization outputs.  
**Detailed Description** Create an HTML Scraper tool and register it with the Tool Registry (P1-13). The tool will take a URL as input, fetch the page's HTML content, and use parsing logic to extract only the main article or body text. It should be designed to strip out common boilerplate elements like navigation links, advertisements, headers, and footers.  
**Refined Acceptance Criteria**  
`Feature: HTML Scraper Tool`

  `Scenario: Extract main content from a news article`  
    `Given the HTML Scraper tool is called with a URL to a news article page`  
    `When the tool successfully fetches and parses the HTML`  
    `Then it returns a string containing only the main body text of the article, excluding navigation links and advertisements`

**Implementation Notes**

* Libraries like BeautifulSoup combined with heuristics can be used for basic scraping. For more robust extraction, consider using a library like trafilatura or goose3, which are specifically designed for this purpose.

### **2.5. Epic: Foundational QA**

This epic establishes the first pillar of the "Multi-Faceted Evaluation Framework" outlined in the blueprint. It creates the infrastructure and assets for automated, objective, and scalable testing of the system's core capabilities.

#### **P1-17 – Create initial BrowseComp benchmark dataset**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Foundational QA |
| **Category** | QA |
| **Effort** | 5 pts |
| **Owner Hint** | PM |
| **Dependencies** | None |

**Strategic Rationale** Simple QA benchmarks are insufficient for testing complex research agents. This CR mandates the creation of a benchmark modeled on OpenAI's BrowseComp, which is specifically designed to test the multi-hop reasoning and information synthesis capabilities that are core to this system. This provides a rigorous, objective measure of the system's fundamental research competency.  
**Detailed Description** Create the first version of an internal benchmark dataset for automated regression testing. The dataset must be designed following the principles of BrowseComp. This involves using an "inverted question" design, where evaluators start with a hard-to-find, verifiable fact and then craft a complex question that requires multi-step research to answer. The answers must be simple (e.g., a name, date, or number) to allow for easy, automated grading.  
**Refined Acceptance Criteria**  
`Feature: Benchmark Dataset Creation`

  `Scenario: The dataset meets quality and quantity standards`  
    `Given the BrowseComp dataset has been created`  
    `When it is reviewed by the QA and Product teams`  
    `Then the dataset contains at least 50 unique question-answer pairs`  
    `And each pair adheres to the "inverted question" and "asymmetry of verification" design principles`

**Implementation Notes**

* The creation of these question-answer pairs requires human creativity and should be a collaborative effort between the Product Management and QA teams.  
* The dataset should be stored in a structured format (e.g., JSON or CSV) and versioned within the mono-repo.

#### **P1-18 – Implement Integration-Test Harness for benchmarks**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Foundational QA |
| **Category** | QA |
| **Effort** | 8 pts |
| **Owner Hint** | QA |
| **Dependencies** | P1-06, P1-17 |

**Strategic Rationale** A benchmark dataset is useless without a harness to run it. This CR creates the automated testing infrastructure that will execute the BrowseComp benchmark against the full system, providing the key pass/fail metrics that track performance over time.  
**Detailed Description** Implement an integration test harness that can programmatically run the entire multi-agent system. The harness must be able to iterate through every question in the BrowseComp-style dataset (P1-17), submit the question to the Supervisor agent, wait for the system to produce a final answer, and then automatically compare the system's answer to the known correct answer to determine a pass or fail.  
**Refined Acceptance Criteria**  
`Feature: Automated Benchmark Execution`

  `Scenario: Run the full benchmark and generate a report`  
    `Given the integration test harness is configured with the BrowseComp dataset`  
    `When the harness is executed`  
    `Then it runs the system against every question in the dataset`  
    `And it outputs a summary report containing the overall pass rate and average execution time per question`

**Implementation Notes**

* The test harness should be integrated into the CI pipeline (P1-02) to run on a regular schedule (e.g., nightly) to detect performance regressions quickly.  
* The harness must have a configurable timeout for each question to prevent stalled runs from blocking the entire test suite.

#### **P1-19 – Create basic unit test framework and coverage goals**

|  |  |
| :---- | :---- |
| **Phase** | 1 |
| **Epic** | Foundational QA |
| **Category** | QA |
| **Effort** | 2 pts |
| **Owner Hint** | QA |
| **Dependencies** | P1-01 |

**Strategic Rationale** While integration tests (P1-18) validate the system as a whole, unit tests are essential for verifying the correctness of individual components in isolation. Establishing a framework and coverage goals enforces a culture of testing discipline, which is critical for maintaining a large and complex codebase.  
**Detailed Description** Establish the standard unit testing framework for the project (e.g., pytest for Python) and integrate it into the development workflow. Set an initial, mandatory code coverage target for all new code. The CI pipeline (P1-02) must be configured to run the coverage analysis and fail the build if the coverage drops below the defined threshold.  
**Refined Acceptance Criteria**  
`Feature: Code Coverage Enforcement`

  `Scenario: CI pipeline fails due to low code coverage`  
    `Given the code coverage threshold is set to 80%`  
    `And a developer opens a pull request that lowers the project's coverage to 75%`  
    `When the CI pipeline runs`  
    `Then the code coverage check fails and the pipeline is marked as "failed"`

**Implementation Notes**

* pytest is the recommended framework for Python due to its rich ecosystem of plugins (e.g., pytest-cov for coverage).  
* The initial coverage target (e.g., 80%) should be realistic but aspirational, and can be adjusted over time. The key is to prevent coverage from decreasing.

## **Part III: Phase 2 \- Advanced Cognition and Evaluation**

This part details the change requests that will give the system a "mind" and the ability to judge its own work. It directly addresses the baseline system's most significant shortcomings: its lack of long-term memory and its inability to perform robust self-correction. The completion of this phase marks the transition from a merely stateful system to a cognitive one.

### **3.1. Epic: Long-Term Memory**

This epic is a cornerstone of the new design, implementing the multi-layered Long-Term Memory (LTM) architecture proposed in the blueprint. It addresses the "Critique of Memory and State Management" by giving the system the ability to learn from its experiences, recall facts, and reuse successful strategies, moving beyond the limitations of a single session's context window. The implementation of an LTM *Service* is a critical architectural decision, decoupling the cognitive function of memory from any single agent and establishing it as a shared, scalable, and centralized system resource.

#### **P2-01 – Implement LTM Service API for memory operations**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Long-Term Memory |
| **Category** | Feature |
| **Effort** | 5 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-13 |

**Strategic Rationale** This CR creates the central gateway for all agent interactions with persistent memory. By defining a formal API for memory operations, it establishes a clean, service-oriented architecture for the system's cognitive functions. This approach ensures that all agents interact with memory in a consistent and manageable way, and it allows the underlying memory technologies to be evolved independently of the agents themselves.  
**Detailed Description** Implement the public-facing API for the Long-Term Memory (LTM) service. This service will expose a set of endpoints (e.g., REST or gRPC) for the three core memory operations: consolidate (write), retrieve (read), and forget (delete). This API will serve as the single, authoritative interface for any agent or system component that needs to interact with the LTM.  
**Refined Acceptance Criteria**  
`Feature: LTM Service API`

  `Scenario: Consolidate a new memory record`  
    `Given the LTM service is running`  
    `When a POST request is sent to the /consolidate endpoint with a valid memory record`  
    `Then the service returns a 201 Created status`

  `Scenario: Retrieve a memory record`  
    `Given a memory record has been previously stored`  
    `When a GET request is sent to the /retrieve endpoint with a relevant query`  
    `Then the service returns the corresponding memory record`

**Implementation Notes**

* The API design should be granular enough to support different memory types (Episodic, Semantic, Procedural) which will be implemented in later CRs. For example, the /consolidate endpoint might accept a memory\_type parameter.  
* The service must be registered as a tool in the Tool Registry (P1-13) so that access can be managed via RBAC.

#### **P2-02 – Integrate vector database for Episodic Memory**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Long-Term Memory |
| **Category** | Infra |
| **Effort** | 5 pts |
| **Owner Hint** | Ops |
| **Dependencies** | P2-01 |

**Strategic Rationale** Episodic Memory, the memory of past experiences, is the foundation for learning from past tasks. A vector database is the ideal technology for this module because it enables efficient semantic search, allowing the system to find past tasks that are conceptually similar, not just keyword-matched. This capability is what allows the system to ask, "Have I solved a problem like this before?".  
**Detailed Description** Provision, configure, and integrate a vector database (e.g., Pinecone, Weaviate, Milvus) to act as the storage backend for the Episodic Memory module of the LTM service. The LTM service (P2-01) will be modified to connect to this database, handling the creation of vector embeddings for incoming episodic memories and executing semantic similarity searches for retrieval requests.  
**Refined Acceptance Criteria**  
`Feature: Episodic Memory Storage`

  `Scenario: Store a memory in the vector database`  
    `Given the LTM service receives a consolidation request for an episodic memory`  
    `When the service processes the request`  
    `Then a corresponding vector embedding is created and stored in the vector database`

**Implementation Notes**

* The choice of embedding model is critical and should be evaluated for its performance on the types of text generated by the system.  
* The infrastructure for the vector database should be managed via infrastructure-as-code (P1-01).

#### **P2-03 – Implement MemoryManager agent for episodic consolidation**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Long-Term Memory |
| **Category** | Feature |
| **Effort** | 5 pts |
| **Owner Hint** | ML |
| **Dependencies** | P2-01 |

**Strategic Rationale** The process of reflecting on a completed task and consolidating it into long-term memory is a distinct cognitive function. This CR creates a specialized MemoryManager agent to handle this responsibility, separating the "doing" of research from the "remembering" of it. This modular design keeps the core research agents focused on their tasks.  
**Detailed Description** Implement a new, specialized agent called the MemoryManager. This agent is designed to run asynchronously after a research task has been completed. It will be triggered with the final State object of the completed graph. Its job is to process this state, package the entire task (query, plan, messages, final report) into a structured "episode," and then call the /consolidate endpoint of the LTM service (P2-01) to store it in Episodic Memory.  
**Refined Acceptance Criteria**  
`Feature: Episodic Memory Consolidation`

  `Scenario: Consolidate a completed task`  
    `Given a research task graph successfully terminates`  
    `When the MemoryManager agent is triggered with the final State object`  
    `Then the agent makes a call to the LTM's /consolidate endpoint with the formatted episode`

**Implementation Notes**

* The trigger for the MemoryManager can be implemented as a final, guaranteed node in the orchestration graph or via an event-driven mechanism that listens for "task completed" events.

#### **P2-04 – Enhance Supervisor to query Episodic LTM for plan templating**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Long-Term Memory |
| **Category** | Feature |
| **Effort** | 5 pts |
| **Owner Hint** | ML |
| **Dependencies** | P2-01, P1-10 |

**Strategic Rationale** Storing memories is useless if they are never used. This CR fundamentally alters the Supervisor agent's behavior by making memory retrieval the *first step* in its planning process. This transforms the agent from being purely reactive to the current query to being knowledge-driven, leveraging past successes to inform future strategies. This is a direct mitigation for the inefficiency of the baseline system, which treats every query as a "cold start".  
**Detailed Description** Modify the core logic of the Supervisor agent (P1-10). Before generating a new research plan, the agent must now first construct a semantic query from the user's request and call the /retrieve endpoint of the LTM service (P2-01). If a similar, highly-rated past task is found, the Supervisor should use the successful plan from that past episode as a template or starting point for generating the new plan.  
**Refined Acceptance Criteria**  
`Feature: LTM-driven Planning`

  `Scenario: Use past plan as a template`  
    `Given a new query is submitted that is semantically similar to a previously successful task`  
    `When the Supervisor agent begins planning`  
    `Then its first action is to call the LTM retrieval endpoint`  
    `And the new plan it generates shares structural similarities with the retrieved plan`

**Implementation Notes**

* The agent's prompt must be updated to include instructions for this new "query LTM first" step.  
* Logic must be included to handle cases where no relevant memories are found, allowing the agent to fall back to generating a plan from scratch.

#### **P2-19 – Research memory consolidation and forgetting strategies**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Long-Term Memory |
| **Category** | Research |
| **Effort** | 5 pts |
| **Owner Hint** | ML |
| **Dependencies** | P2-01 |

**Strategic Rationale** A memory that grows endlessly becomes a liability, filled with outdated, irrelevant, or incorrect information. An effective cognitive system must not only remember but also forget. This research task proactively investigates advanced strategies for memory lifecycle management, ensuring the long-term health and quality of the LTM.  
**Detailed Description** Conduct a research spike into advanced strategies for managing the LTM. The research should cover techniques for automated information value assessment (i.e., deciding what is important enough to store), methods for updating existing memories with new, conflicting information, and algorithms for pruning stale or low-utility memories to prevent the LTM from becoming bloated and unreliable.  
**Refined Acceptance Criteria**  
`Feature: LTM Lifecycle Management Research`

  `Scenario: Deliver research findings`  
    `Given research has been conducted on LTM management`  
    `When a final report is delivered to technical leadership`  
    `Then the report proposes at least two distinct algorithms for managing the LTM lifecycle, with a comparative analysis of their trade-offs`

**Implementation Notes**

* Research should explore concepts from cognitive science, such as spaced repetition and memory decay curves, as potential inspirations for forgetting algorithms.

#### **P2-20 – Implement basic LTM forgetting mechanism**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Long-Term Memory |
| **Category** | Feature |
| **Effort** | 3 pts |
| **Owner Hint** | BE |
| **Dependencies** | P2-01, P2-19 |

**Strategic Rationale** Based on the findings of P2-19, this CR implements an initial, pragmatic version of a forgetting mechanism. This is a crucial first step in maintaining the quality of the LTM, preventing the accumulation of irrelevant data that could degrade retrieval performance and lead to incorrect plan templating.  
**Detailed Description** Implement a basic forgetting mechanism within the LTM service (P2-01). This initial version can be implemented as a scheduled job that runs periodically. It will use simple heuristics to identify and prune memories, such as deleting episodic memories that have not been accessed within a certain time period (e.g., 180 days) or have consistently low evaluation scores.  
**Refined Acceptance Criteria**  
`Feature: LTM Pruning`

  `Scenario: Prune an old, unused memory record`  
    `Given a memory record has a 'last_accessed' timestamp older than N days`  
    `When the scheduled LTM forgetting job runs`  
    `Then the specified record is deleted from the LTM`

**Implementation Notes**

* The forgetting process should perform a "soft delete" first, marking records for deletion before permanently removing them, to allow for a recovery window.

### **3.2. Epic: Self-Correction**

This epic implements the "Evaluator-Optimizer Agent Loop," a core architectural pattern that addresses the "Prompt as Primary Lever" fallacy critiqued in the blueprint. Instead of relying on prompts to prevent errors, this epic builds a system that can architecturally detect and correct them. This is achieved by introducing a dedicated Evaluator agent and a "Chain of Self-Correction" (CoSC) workflow, a more robust approach to error handling than simple self-reflection.

#### **P2-05 – Implement Evaluator agent for critique generation**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Self-Correction |
| **Category** | Feature |
| **Effort** | 3 pts |
| **Owner Hint** | ML |
| **Dependencies** | P1-06 |

**Strategic Rationale** The Evaluator agent is the centerpiece of the self-correction loop. Its existence institutionalizes the act of critique within the workflow. By providing external, structured feedback, the Evaluator enables a far more effective error correction process than simply asking an agent to review its own work.  
**Detailed Description** Implement a new, specialized Evaluator agent. This agent will be a node in the orchestration graph (P1-06). Its role is to receive a piece of generated content (e.g., a summary from the WebResearcher) as input and critique it against a predefined rubric. The agent must be able to identify potential flaws and produce a structured critique object containing specific, actionable feedback and an overall pass/fail score.  
**Refined Acceptance Criteria**  
`Feature: Agent Output Critique`

  `Scenario: Evaluate a piece of text`  
    `Given a piece of text to evaluate is provided as input`  
    `When the Evaluator agent executes`  
    `Then it produces a structured critique object containing specific feedback and a pass/fail score`

**Implementation Notes**

* The Evaluator's system prompt is critical. It must be instructed to be skeptical, meticulous, and to justify its findings with specific reasons.

#### **P2-06 – Implement Evaluator's factual accuracy verification logic**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Self-Correction |
| **Category** | Feature |
| **Effort** | 5 pts |
| **Owner Hint** | ML |
| **Dependencies** | P2-05, P2-09 |

**Strategic Rationale** Factual inaccuracy is one of the most dangerous failure modes for a research agent. This CR equips the Evaluator with the specific capability to verify claims against source material, directly mitigating the risk of hallucination and ensuring the final output is grounded in evidence.  
**Detailed Description** Implement logic within the Evaluator agent (P2-05) to perform factual accuracy verification. The agent must be able to take a generated text (e.g., a summary) and a list of source documents as input. It will then compare each claim in the text against the content of the sources to identify and flag any claims that are unsupported, contradicted, or mis-represented.  
**Refined Acceptance Criteria**  
`Feature: Factual Accuracy Verification`

  `Scenario: Detect an unsupported claim`  
    `Given a summary contains a claim that is not present in its source document`  
    `When the Evaluator agent runs its verification logic`  
    `Then it flags the specific claim as an "unsupported fact" in its critique output`

**Implementation Notes**

* This logic will likely involve using an LLM to perform a series of "question-answering" tasks, where each claim from the summary is turned into a question that is then answered based *only* on the provided source documents.

#### **P2-07 – Implement Evaluator's source quality assessment logic**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Self-Correction |
| **Category** | Feature |
| **Effort** | 3 pts |
| **Owner Hint** | ML |
| **Dependencies** | P2-05 |

**Strategic Rationale** The quality of a research output is heavily dependent on the quality of its sources. This capability allows the system to self-regulate its information-gathering process, learning to prefer authoritative sources over unreliable ones. This is a key aspect of producing trustworthy and high-quality research.  
**Detailed Description** Implement logic within the Evaluator agent (P2-05) to assess the quality of the sources cited in a research output. The agent will use a set of heuristics, likely encoded in its prompt, to assign a quality score to sources. These heuristics should penalize reliance on low-authority domains (e.g., personal blogs, content farms, forums) and reward the use of high-authority domains (e.g., academic journals, official government/company documentation, reputable news organizations).  
**Refined Acceptance Criteria**  
`Feature: Source Quality Assessment`

  `Scenario: Penalize low-quality source`  
    `Given a research output cites only a personal blog as its source`  
    `When the Evaluator agent runs its assessment`  
    `Then its critique output includes a low score for the "Source Quality" criterion`

**Implementation Notes**

* A blocklist/allowlist of domains can be used to supplement the LLM's heuristic judgment.  
* This assessment can be a criterion in the LLM-as-a-Judge rubric (P2-12) as well.

#### **P2-08 – Modify Orchestration Engine to support CoSC feedback loop**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Self-Correction |
| **Category** | Feature |
| **Effort** | 8 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-08, P2-05 |

**Strategic Rationale** This CR connects the pieces of the self-correction mechanism into a functional architectural loop. By modifying the orchestration engine to support the "Generate \-\> Verify \-\> Correct" pattern, it moves self-correction from being a theoretical agent capability to being an enforced, operational workflow.  
**Detailed Description** Modify the Orchestration Engine (P1-06) to enable a Chain of Self-Correction (CoSC) feedback loop. This involves using conditional edges (P1-08). In a typical CoSC graph, a generator agent (e.g., WebResearcher) is followed by the Evaluator agent (P2-05). A conditional edge after the Evaluator will inspect its output in the State object. If the status is 'pass', it routes to the next step in the main workflow. If the status is 'fail', it routes execution back to the original generator agent for another attempt, including the critique as new input.  
**Refined Acceptance Criteria**  
`Feature: Self-Correction Loop`

  `Scenario: Route back for correction on failure`  
    `Given a graph where a Researcher node is followed by an Evaluator node`  
    `When the Researcher produces an output and the Evaluator returns a 'fail' status`  
    `Then the Orchestration Engine routes execution back to the Researcher node for another attempt`

**Implementation Notes**

* The State object (P1-07) must be updated to include the critique from the Evaluator so the generator agent has the necessary feedback for its revision attempt.

#### **P2-09 – Integrate a fact-checking API as an Evaluator tool**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Self-Correction |
| **Category** | Feature |
| **Effort** | 3 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-13, P2-05 |

**Strategic Rationale** The Evaluator cannot always verify claims using only the source documents provided within the task, especially for claims about general world knowledge or recent events. An external fact-checking tool provides an essential, independent reference point, significantly strengthening the Evaluator's ability to detect falsehoods.  
**Detailed Description** Integrate a third-party fact-checking API (e.g., Google Fact Check Tools API or a similar service) as a new tool. This tool must be wrapped in the standard tool interface and registered with the Tool Registry (P1-13). The Evaluator agent (P2-05) will be granted permission to use this tool to validate specific claims that cannot be verified from the provided context alone.  
**Refined Acceptance Criteria**  
`Feature: External Fact-Checking`

  `Scenario: Verify a claim with an external API`  
    `Given the Evaluator agent is checking a claim about a recent world event`  
    `When it uses the fact-checking tool`  
    `Then it receives a credibility rating and supporting links for the claim from the external API`

**Implementation Notes**

* The tool wrapper should handle parsing the API's response into a simple, structured format that the agent can easily interpret (e.g., a JSON object with 'claim', 'rating', 'source\_links').

#### **P2-10 – Develop QA tests for the CoSC loop to prevent infinite cycles**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Self-Correction |
| **Category** | QA |
| **Effort** | 3 pts |
| **Owner Hint** | QA |
| **Dependencies** | P2-08 |

**Strategic Rationale** A feedback loop, while powerful, introduces the risk of infinite cycles, where an agent and an evaluator repeatedly pass a task back and forth without resolution. This test is a critical safeguard to ensure the system has a proper termination condition, preventing resource exhaustion and ensuring stability.  
**Detailed Description** Create a specific integration test designed to validate the termination condition of the CoSC loop (P2-08). The test should configure a scenario where the Evaluator agent is guaranteed to fail an output repeatedly. The test passes if it can verify that the loop correctly terminates after a pre-configured maximum number of retries.  
**Refined Acceptance Criteria**  
`Feature: CoSC Loop Termination`

  `Scenario: Prevent infinite correction loop`  
    `Given an Evaluator agent is configured to always fail an output`  
    `When the CoSC loop is executed`  
    `Then the loop terminates after a pre-configured maximum number of retries (e.g., 3)`

**Implementation Notes**

* The maximum retry count should be stored in the State object and incremented on each loop. The conditional edge logic (P1-08) must check this counter as part of its routing decision.

#### **P2-15 – Research synthetic data generation techniques for self-correction**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Self-Correction |
| **Category** | Research |
| **Effort** | 5 pts |
| **Owner Hint** | ML |
| **Dependencies** | None |

**Strategic Rationale** The blueprint states that self-correction is a learned skill, not just a prompted behavior. To train this skill effectively requires a large, high-quality dataset of errors and corrections. This research task is the first step in creating that dataset, ensuring that the generation methodology is based on state-of-the-art techniques.  
**Detailed Description** Conduct a research spike to investigate and compare state-of-the-art techniques for synthetically generating training data for self-correction tasks. The research should focus on "teacher-student" methodologies, where a powerful "teacher" LLM (e.g., GPT-4o) is used to generate a problem, a flawed solution, a detailed critique of the flaw, and a corrected solution. The goal is to identify a reliable process for creating a large-scale, high-quality dataset.  
**Refined Acceptance Criteria**  
`Feature: Self-Correction Data Generation Research`

  `Scenario: Deliver research findings`  
    `Given research has been conducted on synthetic data generation`  
    `When a final report is delivered to technical leadership`  
    `Then it recommends a specific, state-of-the-art methodology for generating a high-quality self-correction dataset`

**Implementation Notes**

* The research should evaluate the trade-offs between different generation methods in terms of cost, quality, and diversity of the generated examples.

#### **P2-16 – Create synthetic dataset of errors and corrections**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Self-Correction |
| **Category** | ML |
| **Effort** | 5 pts |
| **Owner Hint** | ML |
| **Dependencies** | P2-15 |

**Strategic Rationale** This CR executes the plan developed in P2-15, creating the actual dataset that will be used to explicitly train the Evaluator and other agents to become better at identifying and fixing errors. This is a critical step in moving beyond prompting and towards a system with learned, robust capabilities.  
**Detailed Description** Using the methodology recommended from the research in P2-15, execute a large-scale data generation process to create a synthetic dataset for fine-tuning self-correction abilities. A powerful teacher model will be prompted to generate thousands of examples, with each example comprising an initial problem/task, a flawed initial solution, a step-by-step verification and critique, and a final corrected solution.  
**Refined Acceptance Criteria**  
`Feature: Synthetic Correction Dataset`

  `Scenario: Generate a high-quality dataset`  
    `Given the generation process is complete`  
    `When the dataset is inspected`  
    `Then it contains at least 1,000 high-quality examples, each with an initial solution, a detailed critique, and a corrected solution`

**Implementation Notes**

* The dataset should cover a diverse range of error types (e.g., factual errors, reasoning fallacies, calculation mistakes, formatting issues).  
* Human review of a subset of the generated data is essential to ensure its quality before use in fine-tuning.

#### **P2-17 – Fine-tune Evaluator agent on the correction dataset**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Self-Correction |
| **Category** | ML |
| **Effort** | 8 pts |
| **Owner Hint** | ML |
| **Dependencies** | P2-16 |

**Strategic Rationale** This is the culmination of the self-correction training track. By fine-tuning the Evaluator agent on the purpose-built dataset (P2-16), its ability to detect flaws is transformed from a prompted, heuristic process into a learned, specialized skill. This leads to a more accurate and reliable Evaluator, which in turn improves the quality of the entire system.  
**Detailed Description** Take the synthetic self-correction dataset generated in P2-16 and use it to fine-tune the underlying language model of the Evaluator agent. The fine-tuning task will train the model to take a solution as input and output a critique, or to take a solution and a critique and output a corrected solution. This process explicitly teaches the model the patterns of error identification and correction.  
**Refined Acceptance Criteria**  
`Feature: Evaluator Agent Fine-Tuning`

  `Scenario: Improve flaw detection accuracy`  
    `Given the fine-tuning process is complete`  
    `When the newly fine-tuned Evaluator agent is tested on a holdout set of known flaws`  
    `Then its accuracy at identifying these flaws shows a statistically significant improvement over the base model`

**Implementation Notes**

* A holdout portion of the synthetic dataset must be reserved for evaluation to measure the effectiveness of the fine-tuning process.  
* The fine-tuned model should be versioned and stored in a model registry.

### **3.3. Epic: Evaluation Framework**

This epic builds the second pillar of the multi-faceted evaluation strategy: a robust pipeline for assessing the quality of long-form, free-text outputs. It implements the "Hardened LLM-as-a-Judge Pipeline" proposed in the blueprint, complete with essential safeguards to mitigate the known biases and unreliability of LLM evaluators.

#### **P2-11 – Build LLM-as-a-Judge evaluation pipeline**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Evaluation Framework |
| **Category** | Infra |
| **Effort** | 8 pts |
| **Owner Hint** | Ops |
| **Dependencies** | P1-18 |

**Strategic Rationale** While the BrowseComp benchmark (P1-18) tests for factual recall, many research tasks produce complex, narrative reports that require qualitative assessment. The LLM-as-a-Judge approach provides a scalable method for this evaluation. This pipeline automates the process, enabling frequent and consistent quality assessment of the system's main outputs.  
**Detailed Description** Build an automated pipeline that uses a powerful, state-of-the-art LLM (e.g., GPT-4o, Claude 4 Opus) as an automated evaluator or "judge." The pipeline will take a generated research report and its corresponding source documents as input. It will then query the judge model with a detailed prompt containing a structured rubric (P2-12), and parse and store the resulting scores and justifications.  
**Refined Acceptance Criteria**  
`Feature: LLM-as-a-Judge Pipeline`

  `Scenario: Evaluate a report`  
    `Given a generated report and its source documents`  
    `When the evaluation pipeline is executed`  
    `Then it outputs a single, valid JSON object containing scores and justifications for each criterion in the rubric`

**Implementation Notes**

* The pipeline should be robust to failures in the judge model's API, with retry logic (P4-13) and error handling.  
* The results of the evaluation should be stored in a database or data warehouse for longitudinal analysis of system performance.

#### **P2-12 – Define comprehensive evaluation rubric as a JSON schema**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Evaluation Framework |
| **Category** | Feature |
| **Effort** | 3 pts |
| **Owner Hint** | PM |
| **Dependencies** | P2-11 |

**Strategic Rationale** A judge is only as good as the law it follows. A formal, structured rubric is essential for making the LLM-as-a-Judge pipeline reliable and consistent. Defining this as a JSON schema ensures that the prompt sent to the judge is well-structured and that its output can be parsed programmatically without ambiguity, a key safeguard against unreliability.  
**Detailed Description** Define the detailed evaluation rubric that will be used by the LLM-as-a-Judge (P2-11). The rubric must be defined as a formal JSON schema. It must include, at a minimum, criteria for assessing Factual Accuracy, Completeness, Source Quality, and Coherence. The schema will specify the name, description, data type, and scoring scale for each criterion, which will be used to construct the judge's prompt and validate its response.  
**Refined Acceptance Criteria**  
`Feature: Evaluation Rubric Schema`

  `Scenario: Validate the rubric schema`  
    `Given the JSON schema for the evaluation rubric`  
    `When it is validated against a schema validator`  
    `Then it correctly defines all required evaluation criteria, their descriptions, data types, and scoring scales`

**Implementation Notes**

* The development of the rubric should be a collaborative effort between Product, QA, and Engineering to ensure it captures the desired qualities of a "good" research report.

#### **P2-13 – Curate and label golden dataset of reports for judge calibration**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Evaluation Framework |
| **Category** | QA |
| **Effort** | 8 pts |
| **Owner Hint** | PM |
| **Dependencies** | P2-11 |

**Strategic Rationale** LLM judges are known to have biases and cannot be trusted blindly. A "golden" dataset, manually scored by human experts, is the ground truth against which the LLM judge's performance must be measured. This calibration step is a non-negotiable safeguard to ensure the judge's scores are reliable and aligned with human judgment before they are used to make decisions.  
**Detailed Description** Curate and label a "golden" dataset of research reports. This involves taking a diverse set of reports generated by the system and having multiple human experts manually evaluate them using the exact same rubric defined in P2-12. Each report in the dataset must have detailed, human-generated scores and written justifications for each criterion.  
**Refined Acceptance Criteria**  
`Feature: Golden Dataset for Calibration`

  `Scenario: Review the curated dataset`  
    `Given the golden dataset has been curated and labeled`  
    `When it is reviewed by the QA lead`  
    `Then it contains at least 20 diverse reports with detailed, human-generated scores and justifications for each rubric criterion`

**Implementation Notes**

* At least two human experts should score each report independently to establish inter-annotator agreement and create a more reliable ground truth.

#### **P2-14 – Implement judge calibration test suite against golden dataset**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Evaluation Framework |
| **Category** | QA |
| **Effort** | 5 pts |
| **Owner Hint** | QA |
| **Dependencies** | P2-11, P2-13 |

**Strategic Rationale** This CR closes the loop on judge validation. It creates the automated test that quantifies the LLM judge's reliability by comparing its scores to the human-generated "golden" scores. The output of this test provides a clear metric of judge quality and is used to tune the judge's prompt and configuration until an acceptable level of agreement is reached.  
**Detailed Description** Implement a test suite that automatically runs the LLM-as-a-Judge pipeline (P2-11) against every report in the golden dataset (P2-13). The suite must then calculate a statistical correlation metric (e.g., Cohen's Kappa or Pearson correlation) between the judge's scores and the human scores for each criterion. The output is a report detailing the level of agreement, which is used to detect biases and measure the judge's overall reliability.  
**Refined Acceptance Criteria**  
`Feature: Judge Calibration Suite`

  `Scenario: Measure agreement with human experts`  
    `Given the calibration suite is run against the golden dataset`  
    `When it completes`  
    `Then it outputs a report detailing the agreement score (e.g., kappa > 0.7) between the LLM judge and the human evaluators`

**Implementation Notes**

* Cohen's Kappa is a preferred metric as it accounts for agreement that could occur by chance, making it more robust than simple accuracy.  
* This suite should be re-run whenever the judge model or its prompt is changed to ensure reliability is maintained.

### **3.4. Epic: Orchestration**

This epic adds a crucial safeguard to the orchestration engine, allowing for human oversight and intervention.

#### **P2-18 – Implement a human-in-the-loop breakpoint**

|  |  |
| :---- | :---- |
| **Phase** | 2 |
| **Epic** | Orchestration |
| **Category** | Feature |
| **Effort** | 5 pts |
| **Owner Hint** | UX |
| **Dependencies** | P1-06 |

**Strategic Rationale** Fully autonomous systems can sometimes go astray, especially when faced with ambiguous tasks. A human-in-the-loop (HITL) breakpoint is a critical safety mechanism that allows the system to pause and ask for clarification at key decision points. This prevents task derailment and is a direct mitigation for the "Fail to ask for clarification" (FM-2.2) failure mode identified in the blueprint's MAST analysis.  
**Detailed Description** Implement a special "breakpoint" node type in the Orchestration Engine (P1-06). When the engine executes a node of this type, it must pause the execution of the graph, persist the current State object, and send an alert to a human review queue. The alert must contain the paused state and a user interface for a human operator to inspect the state and provide input to resume the workflow.  
**Refined Acceptance Criteria**  
`Feature: Human-in-the-Loop Intervention`

  `Scenario: Graph pauses for human input`  
    `Given a graph contains a 'human_in_the_loop_breakpoint' node`  
    `When the Orchestration Engine executes that node`  
    `Then the graph execution state is paused`  
    `And an alert is sent to the human review queue with the current State object`

**Implementation Notes**

* The UX for the review queue is a critical component of this task. It should clearly present the current state and provide a simple mechanism for the human to approve, reject, or modify the state before resuming execution.

## **Part IV: Phase 3 \- Dynamic Collaboration and Self-Improvement**

This part of the plan transforms the system from a collection of individual agents into a collaborative team that can learn and improve its own performance over time. It implements the architectural patterns for agent-to-agent communication and the reinforcement learning loop that drives system-level self-improvement.

### **4.1. Epic: Collaboration**

This epic directly addresses what the blueprint identifies as the most critical architectural trade-off of the baseline system: the sacrifice of inter-agent collaboration for the sake of parallelization. By implementing mechanisms for horizontal, peer-to-peer communication inspired by frameworks like AutoGen and CrewAI, these CRs enable more complex and efficient problem-solving and mitigate key communication-based failure modes like "Information Withholding" (FM-2.4).

#### **P3-01 – Implement GroupChatManager for agent collaboration**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Collaboration |
| **Category** | Feature |
| **Effort** | 8 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-06 |

**Strategic Rationale** To overcome the "synchronous execution bottlenecks" of the centralized orchestrator model, agents need a way to communicate directly with each other. The GroupChatManager, inspired by AutoGen, provides this horizontal communication channel. It enables a team of agents to work together on a shared task, coordinating their actions and sharing findings in real-time without needing to route all communication through the Supervisor.  
**Detailed Description** Implement a new special node type in the Orchestration Engine (P1-06) called the GroupChatManager. This manager node will be responsible for facilitating a "group chat" conversation among a specified set of agents. It will manage the turn-taking, pass messages between agents, and decide when the collaborative task is complete, returning the final result to the main graph.  
**Refined Acceptance Criteria**  
`Feature: Agent Group Chat`

  `Scenario: Agent-to-agent message passing`  
    `Given a group chat is initiated with Agent A and Agent B`  
    `When Agent A sends a message into the chat`  
    `Then Agent B receives that message in its next turn within the chat`

**Implementation Notes**

* The GroupChatManager can implement various turn-taking policies, such as a simple round-robin or a more sophisticated policy where an LLM decides which agent should speak next based on the conversation history.

#### **P3-02 – Define agent message passing protocol for group chat**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Collaboration |
| **Category** | Feature |
| **Effort** | 3 pts |
| **Owner Hint** | BE |
| **Dependencies** | P3-01 |

**Strategic Rationale** As agent communication becomes more complex, an unstructured chat can become chaotic. A structured message protocol provides the "grammar" for inter-agent communication, allowing agents to express their intent clearly (e.g., "this is a question," "this is a finding") and address messages to specific peers. This improves the efficiency and clarity of collaboration.  
**Detailed Description** Define and implement a structured, formal protocol for messages passed within the group chat framework (P3-01). The protocol, likely defined as a JSON or Pydantic schema, should support attributes such as message\_type (e.g., 'question', 'finding', 'proposal'), recipient (to allow for directed messages), and content.  
**Refined Acceptance Criteria**  
`Feature: Group Chat Message Protocol`

  `Scenario: Send a directed question`  
    `Given the message protocol is defined`  
    `When Agent A sends a message with type 'question' addressed specifically to Agent B`  
    `Then the recipient agent's context is updated to reflect the directed question from Agent A`

**Implementation Notes**

* The base agent prompt should be updated to instruct agents on how to construct and interpret messages according to this protocol.

#### **P3-03 – Implement hierarchical subgraph spawning for agent teams**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Collaboration |
| **Category** | Feature |
| **Effort** | 8 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-10 |

**Strategic Rationale** Some sub-tasks are themselves too complex for a single agent. The ability to spawn hierarchical teams, inspired by CrewAI, allows the Supervisor to delegate a complex problem to a dedicated, self-contained team of specialists. This team can then execute its own internal workflow, abstracting the complexity away from the main research graph and enabling a more modular and scalable approach to problem decomposition.  
**Detailed Description** Enhance the Orchestration Engine (P1-06) and the Supervisor agent (P1-10) to support the concept of hierarchical subgraphs. The Supervisor should be able to define a node in its plan that, when executed, spawns a new, nested instance of the Orchestration Engine with its own graph of agents. The main graph will pause execution of that branch, wait for the subgraph to complete its entire internal workflow, and then receive the final, consolidated result from the subgraph to continue its own process.  
**Refined Acceptance Criteria**  
`Feature: Hierarchical Agent Teams`

  `Scenario: Spawn a subgraph for a complex task`  
    `Given the Supervisor's plan includes a subgraph node for a complex sub-task`  
    `When the Orchestration Engine executes that node`  
    `Then a new, nested instance of the orchestration engine is created and executed for the subgraph`  
    `And the main graph pauses until the subgraph reports its final result`

**Implementation Notes**

* This feature requires careful state management to pass context down to the subgraph and return the result back up to the parent graph's State object.

#### **P3-04 – Implement a shared collaborative scratchpad**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Collaboration |
| **Category** | Feature |
| **Effort** | 3 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-07, P3-01 |

**Strategic Rationale** Formal message passing (P3-02) can have high overhead. A shared scratchpad provides a low-friction, informal channel for collaboration. It allows agents to share intermediate thoughts, partial results, and raw tool outputs, creating a common context that can facilitate emergent coordination without the need for explicit messaging.  
**Detailed Description** Add a new field, scratchpad, to the central State object (P1-07). This field will be a mutable data structure (e.g., a dictionary or a text block). Within a collaborative context like a group chat (P3-01), any agent can write its intermediate thoughts or data to this shared space. All other agents in the same context can then read from the scratchpad on their subsequent turns.  
**Refined Acceptance Criteria**  
`Feature: Collaborative Scratchpad`

  `Scenario: Share information via scratchpad`  
    `Given two agents are collaborating in a group chat`  
    `When Agent A writes its intermediate findings to the scratchpad field in the State object`  
    `Then Agent B can read the updated content from the scratchpad on its next turn`

**Implementation Notes**

* The scratchpad is particularly useful for sharing large data artifacts, like the full text from a scraped webpage, without cluttering the formal message history.

#### **P3-05 – Develop QA tests for inter-agent communication protocols**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Collaboration |
| **Category** | QA |
| **Effort** | 5 pts |
| **Owner Hint** | QA |
| **Dependencies** | P3-02 |

**Strategic Rationale** Distributed communication is notoriously difficult to get right. This QA task ensures the robustness of the inter-agent communication protocols by creating tests for edge cases like lost messages or network failures. This proactive testing is essential for building a reliable collaborative system.  
**Detailed Description** Create a suite of integration tests designed to validate the robustness and resilience of the inter-agent communication protocols defined in P3-02. These tests should simulate various failure scenarios, including message delivery failure (e.g., network timeout), out-of-order message delivery, and malformed messages, to ensure the system handles these edge cases gracefully.  
**Refined Acceptance Criteria**  
`Feature: Communication Protocol Robustness`

  `Scenario: Handle a lost message`  
    `Given a test scenario is configured to simulate a lost message between two agents`  
    `When the test runs`  
    `Then it verifies that the sending agent's retry logic is correctly triggered after a timeout`

**Implementation Notes**

* These tests will likely require mocking the communication layer to inject faults and simulate failure conditions.

#### **P3-20 – Research emergent communication protocols in group chat**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Collaboration |
| **Category** | Research |
| **Effort** | 8 pts |
| **Owner Hint** | ML |
| **Dependencies** | P3-01 |

**Strategic Rationale** The blueprint suggests that by applying reinforcement learning, the system can encourage the emergence of an effective, implicit collaboration strategy, moving beyond hard-coded interaction patterns. This research investigates how agents might learn their own efficient, task-specific language, a frontier topic in multi-agent systems that could lead to significant performance gains.  
**Detailed Description** Investigate the potential for enabling emergent communication protocols within the group chat framework (P3-01). The research should explore how reinforcement learning could be applied to reward communication patterns that lead to faster or more accurate task completion. The goal is to design a system where agents are incentivized to develop their own efficient, compressed, and task-specific language or communication conventions.  
**Refined Acceptance Criteria**  
`Feature: Emergent Communication Research`

  `Scenario: Deliver proof-of-concept design`  
    `Given the research phase is complete`  
    `When a report is delivered to technical leadership`  
    `Then it includes a detailed proof-of-concept design for an RL environment to train and evaluate emergent communication protocols`

**Implementation Notes**

* The research report should consider the trade-offs between fully emergent protocols and guided evolution, where agents learn within the constraints of a base protocol.

#### **P3-21 – Develop QA tests for race conditions in group chat**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Collaboration |
| **Category** | QA |
| **Effort** | 5 pts |
| **Owner Hint** | QA |
| **Dependencies** | P3-01 |

**Strategic Rationale** Any system with multiple actors modifying a shared state (like the State object's scratchpad) is vulnerable to concurrency issues like race conditions and deadlocks. This QA task is a critical hardening step to ensure the stability and data integrity of the collaborative framework.  
**Detailed Description** Develop a specific suite of integration tests to identify and handle concurrency issues within the GroupChatManager (P3-01). The tests must simulate scenarios where multiple agents attempt to modify the shared State object or communicate simultaneously. The goal is to verify that the system has mechanisms in place (e.g., locking, atomic updates) to prevent data corruption and ensure stable operation under concurrent load.  
**Refined Acceptance Criteria**  
`Feature: Concurrency and Stability`

  `Scenario: Prevent race condition on shared state`  
    `Given a test where two agents attempt to write to the same field in the shared scratchpad simultaneously`  
    `When the test runs`  
    `Then it verifies that a locking mechanism or an atomic update operation prevents data corruption`

**Implementation Notes**

* These tests can be challenging to write and may require specialized libraries for simulating concurrent execution.

### **4.2. Epic: Self-Improvement**

This epic implements the system-level self-improvement loop via Reinforcement Learning from AI Feedback (RLAIF), creating the "flywheel for continuous improvement" described in the blueprint. This is the mechanism that allows the system to learn from its overall performance and optimize its high-level strategies, such as planning.  
The implementation of this epic represents a significant MLOps challenge. It involves orchestrating a complex pipeline where the output of one process (evaluation) becomes the input for the next (reward model training), which in turn produces an artifact (the reward model) used by the final process (policy optimization). This requires more than just individual scripts; it necessitates a robust MLOps workload orchestrator (e.g., Kubeflow, Airflow) to manage the entire DAG of data and model dependencies, ensuring the process is automated, reproducible, and scalable.

#### **P3-06 – Implement Reward Model training pipeline**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Self-Improvement |
| **Category** | ML |
| **Effort** | 13 pts |
| **Owner Hint** | ML |
| **Dependencies** | P2-11 |

**Strategic Rationale** The RLAIF loop requires a reward signal to guide learning. A Reward Model provides this signal by learning to predict the quality of a task's outcome based on its execution trace. This model is the bridge between the evaluation framework and the reinforcement learning algorithm, translating qualitative scores into a quantitative reward that can be used for optimization.  
**Detailed Description** Implement an MLOps pipeline to train a Reward Model. This pipeline will consume the labeled data produced by the LLM-as-a-Judge evaluation pipeline (P2-11), which consists of task execution traces and their corresponding quality scores. The pipeline will use this data to train a model (likely a transformer-based architecture) that takes an execution trace as input and predicts its quality score. The pipeline must handle data preprocessing, model training, evaluation, and versioning.  
**Refined Acceptance Criteria**  
`Feature: Reward Model Training`

  `Scenario: Train a new Reward Model`  
    `Given a dataset of 1,000+ evaluated research task trajectories`  
    `When the training pipeline is run`  
    `Then it outputs a versioned, trained Reward Model artifact to the model registry`

**Implementation Notes**

* The execution trace used for training should include not just the final output, but also key intermediate steps, agent actions, and collaboration metrics (P3-09) to provide rich features for the model.  
* This pipeline should be automated to run periodically as new evaluation data becomes available.

#### **P3-07 – Integrate a PPO library for RLAIF loop**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Self-Improvement |
| **Category** | ML |
| **Effort** | 8 pts |
| **Owner Hint** | ML |
| **Dependencies** | P3-06 |

**Strategic Rationale** Proximal Policy Optimization (PPO) is a state-of-the-art, stable, and sample-efficient reinforcement learning algorithm, making it well-suited for fine-tuning large language models. Integrating a standard PPO library provides the core optimization engine for the RLAIF loop, allowing the system to update agent policies based on the rewards from the Reward Model.  
**Detailed Description** Integrate a standard, well-supported reinforcement learning library (e.g., Hugging Face's TRL, RLlib, or a similar framework) into the system's ML codebase. This involves setting up the necessary components to run the Proximal Policy Optimization (PPO) algorithm. The implementation must be able to take a policy model (the agent's LLM), a trajectory of actions, and the corresponding rewards (from the Reward Model, P3-06) and perform a policy update step.  
**Refined Acceptance Criteria**  
`Feature: RLAIF Policy Update`

  `Scenario: Update a policy model`  
    `Given a policy model, an agent trajectory, and rewards from the Reward Model`  
    `When the PPO algorithm is run for one step`  
    `Then it computes and applies gradients to the policy model's weights`

**Implementation Notes**

* TRL (Transformer Reinforcement Learning) is a strong candidate as it is specifically designed for fine-tuning transformer-based language models.

#### **P3-08 – Connect RLAIF loop to update Supervisor's policy**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Self-Improvement |
| **Category** | ML |
| **Effort** | 5 pts |
| **Owner Hint** | ML |
| **Dependencies** | P3-07, P1-10 |

**Strategic Rationale** This CR connects the RL engine to a specific agent, closing the RLAIF loop for the first time. By targeting the Supervisor's planning policy, this work directly addresses the goal of improving the system's high-level strategic reasoning. Over time, this loop will teach the Supervisor to generate plans that are more likely to lead to high-quality, efficient outcomes.  
**Detailed Description** Connect the PPO-based RLAIF loop (P3-07) to the Supervisor agent's policy model (P1-10). This involves creating a data collection pipeline that logs the trajectories of the Supervisor's planning decisions. These trajectories are then scored by the Reward Model (P3-06), and the resulting rewards are used by the PPO algorithm to fine-tune the Supervisor's underlying LLM, reinforcing planning strategies that correlate with high rewards.  
**Refined Acceptance Criteria**  
`Feature: Supervisor Policy Improvement`

  `Scenario: Improve planning strategy over time`  
    `Given the RLAIF loop has run for several epochs on Supervisor planning data`  
    `When the Supervisor is given a task it previously performed poorly on`  
    `Then its new plan is measurably different and aligns better with high-reward strategies`

**Implementation Notes**

* This process requires careful management of the policy model, the value model (used by PPO), and the reward model, likely all managed within a central model registry.

#### **P3-09 – Log system and collaboration metrics for the Reward Model**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Self-Improvement |
| **Category** | Infra |
| **Effort** | 3 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-05, P3-06 |

**Strategic Rationale** A good outcome is not just about the final report; it's also about the efficiency of the process that produced it. By logging detailed system and collaboration metrics and using them as features for the Reward Model, the system can learn to value not just *what* was produced, but *how* it was produced. This encourages the evolution of more efficient and collaborative behaviors.  
**Detailed Description** Instrument the Orchestration Engine (P1-06) and the GroupChatManager (P3-01) to log detailed system and collaboration metrics as part of the execution trace defined by the tracing schema (P1-05). These metrics should include measures like total token consumption, number of tool calls, number of self-correction loops, communication overhead (e.g., total messages sent in a group chat), and action advancement rate. This enriched trace data will then be fed into the Reward Model training pipeline (P3-06).  
**Refined Acceptance Criteria**  
`Feature: Advanced Metrics Logging`

  `Scenario: Log collaboration efficiency metrics`  
    `Given a group chat task completes`  
    `When the execution trace for that task is examined`  
    `Then it contains structured metrics like 'total_messages_sent', 'average_message_latency', and 'action_advancement_rate'`

**Implementation Notes**

* These metrics should be added as attributes to the root span of the task's trace in OpenTelemetry for easy correlation.

#### **P3-10 – Research SCoRe-based reward shaping for self-correction**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Self-Improvement |
| **Category** | Research |
| **Effort** | 5 pts |
| **Owner Hint** | ML |
| **Dependencies** | P3-06 |

**Strategic Rationale** Standard RL can sometimes reward trivial behaviors. The SCoRe framework provides a more sophisticated approach to reward shaping, specifically designed to encourage meaningful self-corrections. This research investigates how to apply these principles to our RLAIF loop, focusing the learning pressure on acquiring the valuable skill of fixing genuine errors.  
**Detailed Description** Conduct a research spike into reward shaping techniques inspired by the SCoRe (Self-Correction via Reinforcement Learning) framework. The goal is to design a reward function for the RLAIF loop that specifically encourages meaningful self-corrections (e.g., changing a factually incorrect answer to a correct one) over trivial edits (e.g., minor rephrasing) or improving an already-correct answer. This focuses the RL pressure on robust error correction.  
**Refined Acceptance Criteria**  
`Feature: Reward Shaping Research`

  `Scenario: Propose a new reward function`  
    `Given the research phase is complete`  
    `When a report is delivered to technical leadership`  
    `Then it proposes a specific, mathematically defined reward function to be used for training self-correction behavior via RLAIF`

**Implementation Notes**

* The proposed reward function might, for example, provide a large positive reward only if the initial output was 'fail' and the revised output is 'pass'.

### **4.3. Epic: Core Agents & Long-Term Memory**

This group of CRs expands the system's capabilities by introducing new, specialized agents and enriching the Long-Term Memory with a structured, factual knowledge base.

#### **P3-11 – Implement CodeResearcher agent with secure tool use**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Core Agents |
| **Category** | Feature |
| **Effort** | 5 pts |
| **Owner Hint** | ML |
| **Dependencies** | P3-12, P3-18 |

**Strategic Rationale** Many research tasks, particularly in technical domains, require the analysis of source code. The CodeResearcher agent provides this specialized capability, enabling the system to answer questions about software functionality, find bugs, or explain algorithms by directly interacting with code.  
**Detailed Description** Implement a new CodeResearcher agent. This agent specializes in tasks involving code analysis. It must be able to receive a snippet of code, a link to a repository, or a question about a software library. Its primary tool will be a secure code interpreter (P3-18), which it can use to execute code and observe its outputs and errors to inform its reasoning.  
**Refined Acceptance Criteria**  
`Feature: Code Analysis Agent`

  `Scenario: Find a bug in a function`  
    `Given a Python function with a known bug and a task to identify it`  
    `When the CodeResearcher agent executes`  
    `Then it calls the code interpreter tool with the function's code and relevant inputs to trigger the bug`

**Implementation Notes**

* The agent's prompt should be tailored for a senior software engineer persona, instructing it to think about test cases, edge cases, and debugging strategies.

#### **P3-12 – Provision secure code interpreter sandbox environment**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Core Agents |
| **Category** | Infra |
| **Effort** | 8 pts |
| **Owner Hint** | Ops |
| **Dependencies** | None |

**Strategic Rationale** Executing untrusted code generated by an LLM is inherently risky. A secure, isolated sandbox environment is a non-negotiable security requirement for the Code Interpreter tool. This CR provides the critical infrastructure to mitigate the risks of arbitrary code execution, such as file system access or outbound network calls.  
**Detailed Description** Provision and configure a secure, isolated sandbox environment for use by the Code Interpreter tool (P3-18). This should be implemented using lightweight virtualization or containerization technologies with strong security boundaries (e.g., Firecracker, gVisor, or Docker with strict security profiles). The sandbox must be configured to have no network access by default and to have strict limits on CPU, memory, and execution time.  
**Refined Acceptance Criteria**  
`Feature: Secure Code Execution Sandbox`

  `Scenario: Block outbound network access`  
    `Given code is being executed within the sandbox environment`  
    `When that code attempts to make an outbound network call`  
    `Then the operation is blocked by the sandbox and a security error is returned to the agent`

**Implementation Notes**

* Firecracker is an excellent choice for this as it provides VM-level security with container-like speed and efficiency.

#### **P3-13 – Implement Planner agent base class**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Core Agents |
| **Category** | Feature |
| **Effort** | 3 pts |
| **Owner Hint** | ML |
| **Dependencies** | P1-06 |

**Strategic Rationale** While the Supervisor uses high-level reasoning to create a plan, some tasks may benefit from a more structured, optimization-based approach to planning. The Planner agent provides an alternative planning mechanism that formalizes task allocation as an optimization problem, which can lead to more efficient plans for well-defined problems.  
**Detailed Description** Implement the base class for a Planner agent. This agent can be used as an alternative to the Supervisor (P1-09) as the entry point for a research graph. Its role is to take a user query and a set of available resources (e.g., a list of available specialized agents) and produce a structured, executable plan designed to optimize for a specific metric, such as cost or time-to-completion.  
**Refined Acceptance Criteria**  
`Feature: Planner Agent`

  `Scenario: Generate a structured plan`  
    `Given a research query is provided`  
    `When the Planner agent is invoked`  
    `Then it produces a structured plan object that can be executed by the Orchestration Engine`

**Implementation Notes**

* The Planner and Supervisor represent two different philosophies of planning: optimization vs. generative reasoning. The system should be flexible enough to use either, depending on the nature of the task.

#### **P3-14 – Implement greedy algorithm for task allocation in Planner**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Core Agents |
| **Category** | Feature |
| **Effort** | 5 pts |
| **Owner Hint** | ML |
| **Dependencies** | P3-13 |

**Strategic Rationale** This CR implements a first, pragmatic allocation algorithm for the Planner agent. A greedy algorithm, while not always globally optimal, is computationally efficient and often produces very good results. It provides a solid baseline for the Planner's capabilities.  
**Detailed Description** Implement a greedy algorithm within the Planner agent (P3-13) for task allocation. The algorithm will take a list of pending sub-tasks and a pool of available agents (with associated skills or specializations). It will then iterate through the tasks, assigning each one to the available agent that has the highest suitability score or best-predicted performance for that specific task.  
**Refined Acceptance Criteria**  
`Feature: Greedy Task Allocation`

  `Scenario: Assign task to best-fit agent`  
    `Given a list of pending tasks and a pool of agents with different skills`  
    `When the Planner agent runs its allocation algorithm`  
    `Then each task is assigned to the agent with the highest skill match for that task`

**Implementation Notes**

* Agent "skill" can be represented as metadata or even as embeddings, allowing the planner to calculate a similarity score between the task description and the agent's profile.

#### **P3-18 – Implement a basic Code Interpreter tool**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Core Agents |
| **Category** | Feature |
| **Effort** | 5 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-13, P3-12 |

**Strategic Rationale** This tool is the essential capability that empowers the CodeResearcher agent (P3-11). It provides the ability to execute code, which is fundamental for any task involving debugging, verification, or understanding the dynamic behavior of software.  
**Detailed Description** Create and register a Code Interpreter tool with the Tool Registry (P1-13). This tool will accept a string of code (initially supporting Python) and a list of arguments. It will then execute this code within the secure sandbox environment (P3-12) and capture the stdout, stderr, and any final expression value, returning them in a structured object to the calling agent.  
**Refined Acceptance Criteria**  
`Feature: Code Interpreter Tool`

  `Scenario: Execute a simple print statement`  
    `Given the tool receives the code string 'print("hello world")'`  
    `When the tool executes the code in the sandbox`  
    `Then it returns a result object where the 'stdout' field is equal to "hello world"`

**Implementation Notes**

* The tool must enforce strict timeouts to prevent long-running or infinite-looping code from consuming resources.

#### **P3-19 – Implement a GitHub Search API tool**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Core Agents |
| **Category** | Feature |
| **Effort** | 2 pts |
| **Owner Hint** | BE |
| **Dependencies** | P1-13 |

**Strategic Rationale** To effectively research software, agents need to be able to find it. This tool provides a structured interface to the GitHub API, allowing agents like the CodeResearcher to programmatically search for relevant repositories, files, or code snippets, a much more efficient approach than trying to navigate the GitHub website via a generic web browser.  
**Detailed Description** Create and register a GitHub Search tool with the Tool Registry (P1-13). This tool will act as a wrapper around the GitHub REST API, providing functions for searching for repositories, code, and issues. The wrapper must handle authentication and parse the API responses into a clean, agent-friendly format.  
**Refined Acceptance Criteria**  
`Feature: GitHub Search Tool`

  `Scenario: Search for a repository`  
    `Given a query for a specific open-source library`  
    `When the GitHub Search tool is called with the query`  
    `Then it returns a list of relevant repository URLs and descriptions`

**Implementation Notes**

* The tool should respect the API rate limits of the GitHub API and implement appropriate backoff logic.

#### **P3-15 – Integrate graph database for Semantic LTM**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Long-Term Memory |
| **Category** | Infra |
| **Effort** | 5 pts |
| **Owner Hint** | Ops |
| **Dependencies** | P2-01 |

**Strategic Rationale** Semantic Memory—the memory of facts and their relationships—is the system's internal, trusted knowledge base. A graph database (e.g., Neo4j) is the ideal technology for this module because it is purpose-built for storing and querying highly connected data, making it perfect for representing a knowledge graph.  
**Detailed Description** Provision, configure, and integrate a graph database (e.g., Neo4j, Neptune) to serve as the backend for the LTM's Semantic Memory module. The LTM service (P2-01) will be enhanced to connect to this database. It will handle requests to store new facts (as nodes and relationships) and to query the knowledge graph for information.  
**Refined Acceptance Criteria**  
`Feature: Semantic Memory Storage`

  `Scenario: Store a factual relationship`  
    `Given the LTM service receives a request to store a fact (e.g., subject, predicate, object)`  
    `When it processes the request for the Semantic Memory module`  
    `Then a corresponding node and relationship are created in the graph database`

**Implementation Notes**

* The choice of graph schema (e.g., property graph model) is a key design decision that will affect query performance and flexibility.

#### **P3-16 – Enhance MemoryManager to extract entities for knowledge graph**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Long-Term Memory |
| **Category** | Feature |
| **Effort** | 8 pts |
| **Owner Hint** | ML |
| **Dependencies** | P2-03, P3-15 |

**Strategic Rationale** This CR gives the system the ability to autonomously grow its own knowledge base. By enhancing the MemoryManager to extract entities and relationships from verified research, it creates a virtuous cycle: better research leads to a better knowledge graph, which in turn leads to better, more efficient future research.  
**Detailed Description** Enhance the MemoryManager agent (P2-03) with Named Entity Recognition (NER) and Relation Extraction capabilities. After a research task is completed and the final report has been verified by the Evaluator, the MemoryManager will process this high-quality text to identify key entities (e.g., people, organizations, technologies) and the relationships between them. It will then call the LTM service (P2-01) to populate these facts into the Semantic Memory knowledge graph (P3-15).  
**Refined Acceptance Criteria**  
`Feature: Knowledge Graph Population`

  `Scenario: Extract and store a relationship`  
    `Given a verified report contains the sentence "Apple acquired NeXT in 1997"`  
    `When the MemoryManager agent processes this report`  
    `Then it adds nodes for 'Apple' and 'NeXT' with an 'ACQUIRED' relationship (with a 'year' property of 1997) to the knowledge graph`

**Implementation Notes**

* This capability will require a sophisticated LLM prompt that instructs the model to act as a knowledge extraction engine and to output the results in a structured format (e.g., a list of subject-predicate-object triples).

#### **P3-17 – Implement agent query path for Semantic LTM**

|  |  |
| :---- | :---- |
| **Phase** | 3 |
| **Epic** | Long-Term Memory |
| **Category** | Feature |
| **Effort** | 3 pts |
| **Owner Hint** | BE |
| **Dependencies** | P3-15 |

**Strategic Rationale** This CR modifies core agent behavior to leverage the newly created Semantic LTM. By checking the internal knowledge graph first, agents can get trusted, low-latency answers to factual questions, reducing their reliance on expensive and potentially unreliable external tool calls (like web search). This directly addresses the "high token consumption" and hallucination risks of the baseline system.  
**Detailed Description** Modify the base logic of all information-seeking agents (e.g., WebResearcher, Supervisor). When an agent needs to find a specific piece of factual information, its decision-making process must be updated to first query the Semantic LTM (P3-15). Only if the internal knowledge graph does not contain the answer should the agent proceed to use an external tool like web\_search.  
**Refined Acceptance Criteria**  
`Feature: Knowledge-driven Action`

  `Scenario: Prioritize internal knowledge`  
    `Given an agent needs to find a specific fact, like "the capital of France"`  
    `When the agent executes its turn`  
    `Then its first action is to query the Semantic LTM service before attempting an external web search`

**Implementation Notes**

* This can be implemented by adding a "knowledge graph search" tool to the agents' permitted tool list and instructing them in their system prompts to prefer it for factual queries.

## **Part V: Phase 4 \- Production Hardening and Specialization**

This final phase focuses on optimizing the system for efficiency, reliability, and advanced capabilities, preparing it for production deployment. It introduces mechanisms for skill acquisition (Procedural Memory), fosters agent specialization to combat performance plateaus, and implements the final layers of production-grade resilience and quality assurance.

### **5.1. Epic: Performance Tuning**

This epic introduces the third layer of the LTM, Procedural Memory, which is the memory of "skills." By learning and reusing successful action sequences, the system can dramatically improve its efficiency, reliability, and speed on previously seen tasks.

#### **P4-01 – Implement Procedural Memory module in LTM Service**

|  |  |
| :---- | :---- |
| **Phase** | 4 |
| **Epic** | Performance Tuning |
| **Category** | Feature |
| **Effort** | 5 pts |
| **Owner Hint** | BE |
| **Dependencies** | P2-01 |

**Strategic Rationale** Procedural Memory allows the system to move beyond just remembering facts and experiences to remembering *how to do things*. This is a powerful optimization that allows agents to learn and reuse complex "skills," such as a multi-step tool-use chain, instead of reasoning from scratch each time.  
**Detailed Description** Implement the Procedural Memory module within the LTM service (P2-01). This involves creating a new data store (which could be a simple key-value store or a document database) and exposing new API endpoints or enhancing existing ones for storing and retrieving "procedures." A procedure is defined as a successful, generalizable sequence of actions (primarily tool calls).  
**Refined Acceptance Criteria**  
`Feature: Procedural Memory Storage`

  `Scenario: Store a successful procedure`  
    `Given the LTM service receives a request to store a new procedure`  
    `When it processes the request`  
    `Then the sequence of actions is successfully saved in the procedural memory store`

**Implementation Notes**

* Procedures should be stored with metadata describing the task goal they achieve, which can be used for effective retrieval.

#### **P4-02 – Instrument agents to identify and store successful tool sequences**

|  |  |
| :---- | :---- |
| **Phase** | 4 |
| **Epic** | Performance Tuning |
| **Category** | Feature |
| **Effort** | 5 pts |
| **Owner Hint** | ML |
| **Dependencies** | P4-01 |

**Strategic Rationale** This CR implements the "skill acquisition" mechanism. It gives agents the ability to recognize when they have successfully completed a task using a sequence of tools and to propose that sequence for consolidation into Procedural Memory. This is how the system learns new skills from its successful actions.  
**Detailed Description** Instrument the base agent class to log the sequence of tool calls it makes during a task. When a task branch concludes successfully (as determined by the Evaluator or another success condition), this new logic will analyze the sequence of tool calls. It will then attempt to generalize this sequence into a reusable "procedure" and send it to the MemoryManager agent for consolidation into Procedural Memory (P4-01).  
**Refined Acceptance Criteria**  
`Feature: Skill Acquisition`

  `Scenario: Identify and store a new skill`  
    `Given an agent successfully uses a sequence of three tools to complete a task`  
    `When the task finishes successfully`  
    `Then a new procedure containing those three tool calls is sent to the LTM service for storage`

**Implementation Notes**

* The generalization logic is key. It should try to replace specific arguments with placeholders to make the procedure more broadly applicable. For example, web\_search(query="Transformer architecture") might be generalized to web\_search(query=$topic).

#### **P4-03 – Enhance agents to query and execute stored procedures**

|  |  |
| :---- | :---- |
| **Phase** | 4 |
| **Epic** | Performance Tuning |
| **Category** | Feature |
| **Effort** | 5 pts |
| **Owner Hint** | ML |
| **Dependencies** | P4-01 |

**Strategic Rationale** This CR completes the skill-learning loop by enabling agents to *use* the skills stored in Procedural Memory. By executing a stored procedure, an agent can bypass costly and time-consuming reasoning from scratch, leading to significant improvements in performance, reliability, and cost-efficiency for recurring tasks.  
**Detailed Description** Modify the agent's decision-making logic to query Procedural Memory at the start of a task. If a relevant, stored procedure is found, the agent should execute the pre-defined sequence of actions instead of reasoning from scratch, improving efficiency and reliability.\[1\]

* **Acceptance Criteria:**  
  `Feature: Skill Execution`  
    `Scenario: Execute a stored procedure`  
      `Given a new task is assigned to an agent that matches a stored procedure in LTM`  
      `When the agent begins its turn`  
      `Then it retrieves and executes the procedure's action sequence directly without further reasoning`

#### **P4-04 – Add LTM hit-rate metrics to observability dashboard**

* **Phase:** 4  
* **Epic:** Performance Tuning  
* **Category:** Infra  
* **Effort:** 3 pts  
* **Owner Hint:** FE  
* **Dependencies:** P1-04, P2-01  
* **Description:** Add widgets to the main observability dashboard to track LTM hit rates for each memory type (Episodic, Semantic, Procedural). This provides a clear, at-a-glance view of how effectively the LTM is being leveraged to reduce redundant work and external API calls.\[1\]  
* **Acceptance Criteria:**  
  `Feature: LTM Performance Monitoring`  
    `Scenario: View LTM hit rates`  
      `Given the system is running and processing tasks`  
      `When an operator views the main observability dashboard`  
      `Then they can see a time-series graph displaying the hit rate for each LTM type`

#### **P4-05 – Research RAG vs fine-tuning for procedural memory recall**

* **Phase:** 4  
* **Epic:** Performance Tuning  
* **Category:** Research  
* **Effort:** 5 pts  
* **Owner Hint:** ML  
* **Dependencies:** P4-01  
* **Description:** Conduct a research spike to compare two approaches for teaching agents to use procedural memory: Retrieval-Augmented Generation (RAG) where procedures are injected into the context, versus fine-tuning the agent's model to learn procedures implicitly. The goal is to determine the most effective and efficient method.\[1\]  
* **Acceptance Criteria:**  
  `Feature: Procedural Memory Recall Research`  
    `Scenario: Deliver research findings`  
      `Given the research spike is complete`  
      `When a report is delivered to technical leadership`  
      `Then it provides a data-backed recommendation on whether to use RAG, fine-tuning, or a hybrid approach for procedural memory`

### **Epic: Agent Specialization**

#### **P4-06 – Build MLOps pipeline for parallel multi-agent fine-tuning**

* **Phase:** 4  
* **Epic:** Agent Specialization  
* **Category:** ML  
* **Effort:** 13 pts  
* **Owner Hint:** Ops  
* **Dependencies:** P3-08  
* **Description:** Build an MLOps pipeline to support multi-agent fine-tuning. The pipeline must be able to manage a "society" of agents, collect successful trajectories for each individual, and then independently fine-tune each agent only on its own data to encourage specialization.\[1\]  
* **Acceptance Criteria:**  
  `Feature: Multi-Agent Finetuning Pipeline`  
    `Scenario: Run parallel fine-tuning jobs`  
      `Given a pool of five distinct WebResearcher agents`  
      `When the multi-agent fine-tuning pipeline is executed`  
      `Then it triggers five separate fine-tuning jobs, one for each agent, using only that agent's collected data`

#### **P4-07 – Modify Supervisor to select agents from a diverse, specialized pool**

* **Phase:** 4  
* **Epic:** Agent Specialization  
* **Category:** Feature  
* **Effort:** 5 pts  
* **Owner Hint:** ML  
* **Dependencies:** P4-06  
* **Description:** Modify the Supervisor (or Planner) agent's task allocation logic. Instead of assuming a single agent for each role, it must now select the most appropriate agent from a diverse pool of fine-tuned specialists based on task requirements and agent metadata.\[1\]  
* **Acceptance Criteria:**  
  `Feature: Specialist Agent Selection`  
    `Scenario: Select a financial specialist`  
      `Given a task requires analyzing a 10-K report`  
      `And a pool of WebResearcher agents contains one that has specialized in financial topics`  
      `When the Supervisor allocates the task`  
      `Then it selects the financial specialist agent for the job`

#### **P4-08 – Develop agent policy divergence and specialization metrics**

* **Phase:** 4  
* **Epic:** Agent Specialization  
* **Category:** QA  
* **Effort:** 3 pts  
* **Owner Hint:** QA  
* **Dependencies:** P4-06  
* **Description:** Develop a set of metrics to quantify the diversity of policies within a pool of specialized agents. This could involve measuring the cosine distance between agent embeddings or their response dissimilarity on a benchmark task. These metrics will verify that the fine-tuning process is successfully creating specialization.\[1\]  
* **Acceptance Criteria:**  
  `Feature: Specialization Measurement`  
    `Scenario: Track policy divergence`  
      `Given the multi-agent fine-tuning pipeline has run over several cycles`  
      `When the policy divergence metrics are calculated`  
      `Then the resulting report shows a measurable increase in policy divergence among the agent pool over time`

### **Epic: Production Hardening**

#### **P4-09 – Implement CitationAgent with source-claim matching logic**

* **Phase:** 4  
* **Epic:** Production Hardening  
* **Category:** Feature  
* **Effort:** 8 pts  
* **Owner Hint:** ML  
* **Dependencies:** None  
* **Description:** Implement the CitationAgent. Its core logic must be able to scan a final draft report and the list of source documents. For each claim in the report, it must perform a semantic search to find the exact passage in the sources that supports the claim.\[1\]  
* **Acceptance Criteria:**  
  `Feature: Source-Claim Matching`  
    `Scenario: Find supporting evidence for a claim`  
      `Given a sentence in a final report and a set of source documents`  
      `When the CitationAgent runs its matching logic`  
      `Then it correctly identifies and returns the specific source document and passage that supports the sentence`

#### **P4-10 – Implement citation formatting based on specified styles**

* **Phase:** 4  
* **Epic:** Production Hardening  
* **Category:** Feature  
* **Effort:** 3 pts  
* **Owner Hint:** BE  
* **Dependencies:** P4-09  
* **Description:** Enhance the CitationAgent to format the matched source-claim pairs into proper citations. The agent should support multiple standard citation styles (e.g., APA, MLA) and correctly insert them into the final report text.\[1\]  
* **Acceptance Criteria:**  
  `Feature: Citation Formatting`  
    `Scenario: Format a citation in APA style`  
      `Given a matched source-claim pair and a specified style of 'APA'`  
      `When the CitationAgent formats the citation`  
      `Then the output string adheres to the APA citation format rules`

#### **P4-11 – Integrate CitationAgent as a final, mandatory graph node**

* **Phase:** 4  
* **Epic:** Production Hardening  
* **Category:** Feature  
* **Effort:** 3 pts  
* **Owner Hint:** BE  
* **Dependencies:** P1-10, P4-09  
* **Description:** Modify the Supervisor's planning logic to ensure that the CitationAgent is always included as one of the final nodes in any research graph. This makes proper citation a mandatory, non-skippable step in the workflow, ensuring academic integrity.\[1\]  
* **Acceptance Criteria:**  
  `Feature: Mandatory Citation Step`  
    `Scenario: Verify citation agent in plan`  
      `Given any research plan generated by the Supervisor`  
      `When the graph definition is inspected`  
      `Then it contains a CitationAgent node that is guaranteed to run before the final termination node`

#### **P4-12 – Implement state checkpointing for robust fault recovery**

* **Phase:** 4  
* **Epic:** Production Hardening  
* **Category:** Infra  
* **Effort:** 5 pts  
* **Owner Hint:** BE  
* **Dependencies:** P1-07  
* **Description:** Implement robust state checkpointing in the Orchestration Engine. After every node execution, the complete State object must be durably persisted. This allows a long-running workflow to be resumed from the last successful step in case of a system crash or transient failure.\[1\]  
* **Acceptance Criteria:**  
  `Feature: Fault Recovery`  
    `Scenario: Resume a failed workflow`  
      `Given a graph execution fails at step N due to a system crash`  
      `When the task is manually or automatically resumed`  
      `Then the Orchestration Engine loads the state from the last successful checkpoint (N-1) and restarts execution from step N`

#### **P4-13 – Implement exponential backoff and retry logic in tool calls**

* **Phase:** 4  
* **Epic:** Production Hardening  
* **Category:** Feature  
* **Effort:** 3 pts  
* **Owner Hint:** BE  
* **Dependencies:** P1-13  
* **Description:** Add exponential backoff and retry logic to the wrappers for all external tool calls. This makes agents more resilient to transient network issues or temporary API rate limits, preventing an entire research task from failing due to a single, recoverable error.\[1\]  
* **Acceptance Criteria:**  
  `Feature: Tool Call Resilience`  
    `Scenario: Recover from a transient API error`  
      `Given a tool call fails with a transient error code (e.g., 503 Service Unavailable)`  
      `When the agent's logic proceeds`  
      `Then it automatically retries the tool call after a short, exponentially increasing delay`

#### **P4-14 – Develop MAST test for Step Repetition (FM-1.3)**

* **Phase:** 4  
* **Epic:** Production Hardening  
* **Category:** QA  
* **Effort:** 3 pts  
* **Owner Hint:** QA  
* **Dependencies:** P1-18, P2-04  
* **Description:** Create an integration test based on the MAST taxonomy to detect unnecessary step repetition (FM-1.3). The test will give the system a task, and then a nearly identical subsequent task, verifying that the system uses its Episodic Memory instead of repeating the entire workflow.\[1\]  
* **Acceptance Criteria:**  
  `Feature: Step Repetition Resilience (MAST FM-1.3)`  
    `Scenario: Reuse past results`  
      `Given a task has been successfully solved and stored in Episodic LTM`  
      `When a nearly identical task is submitted`  
      `Then the execution trace shows a hit on Episodic LTM and a significantly shorter workflow with fewer tool calls`

#### **P4-15 – Develop MAST test for Information Withholding (FM-2.4)**

* **Phase:** 4  
* **Epic:** Production Hardening  
* **Category:** QA  
* **Effort:** 5 pts  
* **Owner Hint:** QA  
* **Dependencies:** P1-18, P3-01  
* **Description:** Create an integration test to provoke Information Withholding (FM-2.4). The test will require collaboration between two agents in a group chat but provide a critical piece of information only to the first agent. The test passes if the information is successfully shared.\[1\]  
* **Acceptance Criteria:**  
  `Feature: Information Withholding Resilience (MAST FM-2.4)`  
    `Scenario: Share critical information in a group chat`  
      `Given Agent A is collaborating with Agent B in a group chat`  
      `And Agent A possesses a critical fact required to solve the task`  
      `When the collaborative task is executed`  
      `Then the final output produced by Agent B correctly incorporates the critical fact from Agent A`

#### **P4-16 – Develop MAST test for Incorrect Verification (FM-3.3)**

* **Phase:** 4  
* **Epic:** Production Hardening  
* **Category:** QA  
* **Effort:** 5 pts  
* **Owner Hint:** QA  
* **Dependencies:** P1-18, P2-06  
* **Description:** Create an integration test for Incorrect Verification (FM-3.3). The test will provide a research task where the most easily accessible source contains a subtle factual error. The test passes if the Evaluator agent's verification process successfully identifies and flags the error.\[1\]  
* **Acceptance Criteria:**  
  `Feature: Incorrect Verification Resilience (MAST FM-3.3)`  
    `Scenario: Detect a factual error in a source`  
      `Given a research task where the primary source contains a known factual error`  
      `When the Evaluator agent critiques the research output based on that source`  
      `Then its critique explicitly identifies and flags the specific factual error`

#### **P4-17 – Expand Tool Registry with specialized database connectors**

* **Phase:** 4  
* **Epic:** Production Hardening  
* **Category:** Feature  
* **Effort:** 5 pts  
* **Owner Hint:** BE  
* **Dependencies:** P1-13  
* **Description:** Expand the Tool Registry with a set of specialized and robust connectors for querying common structured databases (e.g., SQL, GraphQL). This allows agents to perform research on internal, proprietary data sources, not just the public web.\[1\]  
* **Acceptance Criteria:**  
  `Feature: Structured Data Tooling`  
    `Scenario: Query a SQL database`  
      `Given a SQL Query tool is registered in the Tool Registry`  
      `When an authorized agent calls it with a valid SQL query`  
      `Then it receives the query results in a structured format (e.g., JSON)`

#### **P4-18 – Research spatio-temporal memory structures**

* **Phase:** 4  
* **Epic:** Long-Term Memory  
* **Category:** Research  
* **Effort:** 8 pts  
* **Owner Hint:** ML  
* **Dependencies:** P2-01  
* **Description:** Conduct research into advanced memory structures, specifically spatio-temporal memory. This research will explore how to augment the LTM to track how information evolves over time and across different contexts, enabling more nuanced reasoning about dynamic topics.\[1\]  
* **Acceptance Criteria:**  
  `Feature: Advanced Memory Research`  
    `Scenario: Design a spatio-temporal memory module`  
      `Given the research phase is complete`  
      `When a report is delivered to technical leadership`  
      `Then it proposes a detailed data model and API design for a spatio-temporal memory module capable of versioning facts over time`
