# **agentic-research-engine: A Self-Improving Multi-Agent Research System**

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/actions)
[![Coverage](https://img.shields.io/badge/coverage-20%25-red)](https://codecov.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## **1. Vision & Mission**

The agentic-research-engine is a next-generation multi-agent research system designed to transcend the limitations of current agentic paradigms. Our mission is to build a system capable of genuine learning, dynamic collaboration, and autonomous self-improvement, moving beyond the rigid orchestrator-worker models that are stateful but static.
This system is architected to address critical challenges in agentic AI, including coordination complexity, high operational cost, and the inability to learn from experience. By integrating advanced cognitive architectures with flexible collaboration protocols, the agentic-research-engine aims to become a true partner in the complex processes of research, discovery, and engineering.

For the complete implementation blueprint, see [BLUEPRINT.md](BLUEPRINT.md).

## **2. Core Architectural Pillars**

The architecture of the agentic-research-engine is founded on four key pillars that ensure robustness, intelligence, and adaptability :

1. **Hybrid Graph-Based Supervisor Model**: We abandon rigid, centralised control in favour of a dynamic, stateful graph for workflow management, inspired by LangGraph. This provides explicit control, deep observability, and resilience against failure.
2. **Multi-Layered Long-Term Memory (LTM)**: To enable genuine cognition, the system incorporates a dedicated memory service that distinguishes between:
   * **Episodic Memory**: For learning from past tasks and experiences.
   * **Semantic Memory**: A trusted internal knowledge graph of verified facts.
   * **Procedural Memory**: For acquiring and reusing successful "skills" or action sequences.
  * A scheduled Kubernetes CronJob calls the LTM `forget` API nightly to remove
    stale episodic records based on stored timestamps. The job emits a
    `ltm.deletions` metric for monitoring.
3. **Institutionalised Self-Correction Loop**: Moving beyond ineffective self-reflection, the system institutionalises a formal critique-and-refinement process. A dedicated Evaluator agent provides external feedback on agent outputs, driving an iterative correction cycle to ensure high-quality, reliable results.
4. **Multi-Faceted Evaluation Framework**: System performance is measured through a comprehensive framework that assesses not only task accuracy (via a BrowseComp-style benchmark) but also output quality, source fidelity, and collaboration efficiency. This data feeds a Reinforcement Learning from AI Feedback (RLAIF) loop, enabling the system to continuously improve its own policies.

## **3. System Workflow Example**

To understand how these pillars work in concert, consider a query like: *"Analyse the performance impact of the Transformer architecture compared to LSTMs for long-sequence NLP tasks."* 

1. **Planning & LTM Query (Supervisor)**: The Supervisor receives the query. It first queries its **Episodic Memory** for similar past tasks and its **Semantic Memory** for core concepts like "Transformer" and "LSTM" to build initial context. It then constructs a research graph with parallel subgraphs for "Core Performance Comparison" and "Architectural Innovations for Long-Range Memory".
2. **Parallel Execution & Collaboration (Agent Teams)**: The Orchestration Engine executes the graph. For the "Innovations" subgraph, a team of a WebResearcher and a CodeResearcher is formed. They use a **dynamic group chat** to collaborate, sharing papers and code analysis on a shared scratchpad.
3. **Verification & Self-Correction (Evaluator)**: The team's summary is passed to the Evaluator agent. The Evaluator finds a minor misrepresentation and routes the task back with a critique. The team receives the feedback, corrects its summary, and resubmits for approval.
4. **Synthesis & Citation (Supervisor & CitationAgent)**: Once all subgraphs are complete and verified, the Supervisor synthesizes the findings into a coherent report. This draft is then passed to the mandatory CitationAgent, which ensures every claim is accurately attributed to its source.
5. **Memory Consolidation (MemoryManager)**: After the final report is delivered, the MemoryManager agent processes the entire task, consolidating the experience into Episodic Memory and extracting new, verified facts for the Semantic Memory knowledge graph.

## **4. Repository Structure**

This is a mono-repo containing all services, agent definitions, and infrastructure code for the agentic-research-engine.
```
/
├── agents/             # Source code for individual agent implementations (e.g., Supervisor, Evaluator)
├── services/           # Backend services for core cognitive modules
│   ├── ltm_service/    # The Long-Term Memory service
│   └── tool_registry/  # The secure Tool Registry service
├── engine/             # The core graph-based Orchestration Engine
├── tools/              # Wrappers for external tools (e.g., Web Search, PDF Reader)
├── infra/              # Infrastructure-as-Code (e.g., Terraform, Docker configs)
├── pipelines/          # CI/CD and MLOps pipeline definitions
├── notebooks/          # Jupyter notebooks for research, data analysis, and experimentation
├── tests/              # Unit, integration, and benchmark tests
│   ├── unit/
│   └── integration/
└── docs/               # Project documentation, including the full Change Request Ledger
```

The versioned OpenAPI schema for the LTM service is stored at
[`docs/api/ltm_openapi.yaml`](docs/api/ltm_openapi.yaml). See
[`docs/api.md`](docs/api.md) for details on how to regenerate the specification.

## **5. Getting Started**

### **Prerequisites**

* Python 3.10+
* Poetry (for dependency management)
* Docker and Docker Compose
* pre-commit

### **Development Setup**

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd agentic-research-engine
   ```

   It's recommended to work inside a virtual environment or
   the provided devcontainer:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   ```

2. **Install dependencies and tools:**
   ```bash
   bash scripts/setup_dev_env.sh
   ```
  The setup script installs from `requirements.txt` using a
  pinned `constraints.txt` file to avoid dependency resolution loops.
  A compiled `requirements.lock` is provided for fully reproducible installs.
   It pulls the CPU-only PyTorch wheels so you don't need CUDA
   drivers for local testing.
   Optional features like LangSmith integration and TRL-based policy
   optimisation can be installed later:
   ```bash
   pip install langsmith trl
   ```
   For a lean environment run `bash scripts/bootstrap_minimal.sh`. See the
   [Minimal Setup section](docs/onboarding.md#minimal-setup) for troubleshooting
   tips.

3. **Configure environment variables:** Copy the example environment file and populate it with the necessary API keys and configuration values.
   ```bash
   cp .env.example .env
   # Now, edit .env with your credentials
   ```
   If you're behind a proxy set `HTTP_PROXY` and `HTTPS_PROXY`. To target a
   specific GPU use `CUDA_VISIBLE_DEVICES`.

4. **Launch core services:** The repository provides a `docker-compose.yml` that
   starts an OpenTelemetry collector, a Weaviate vector database, and a Jaeger backend.
   Set `ENVIRONMENT` and `SERVICE_VERSION` in your shell to tag telemetry data, then
   bring the stack up:
   ```bash
   ENVIRONMENT=dev SERVICE_VERSION=0.2.3 docker-compose up -d
   ```

## Configuration

Copy `.env.example` to `.env` and update the values for your environment. Common
variables include `OPENAI_API_KEY`, proxy settings and optional integrations
such as LangSmith. Refer to
[docs/onboarding.md#environment-variables](docs/onboarding.md#environment-variables)
for a full list and guidance.


## **6. Development Setup**

Run the helper script to install Python packages (including `tenacity`) and set
up pre-commit hooks:

```bash
bash scripts/setup_dev_env.sh
```

## **7. Running Tests**

A comprehensive test suite is crucial for maintaining system quality.

Before running tests, make sure all Python dependencies are installed. The
`setup_dev_env.sh` helper installs packages from `requirements.txt` (including
the `tenacity` library required by several pipelines) and sets up pre-commit hooks:

```bash
bash scripts/setup_dev_env.sh
```

For a quick subset run only the core tests:

```bash
pytest -m "core"
```
See [docs/testing.md#running-core-tests-only](docs/testing.md#running-core-tests-only) for more details.

### **Unit Tests**

Unit tests verify individual components in isolation. They are located in `tests/unit/`.

```
poetry run pytest tests/unit/
```

### **Integration Tests**

Integration tests verify the interactions between different components and services. They are located in `tests/integration/`.

```
poetry run pytest tests/integration/
```

### **Benchmark Evaluation**

The full system benchmark (P1-18), which evaluates end-to-end research capabilities, can be run via a dedicated script.

```
poetry run python -m tests.run_benchmark --benchmark=browsecomp_v1
```

### **PDF Reader Tool**

The `pdf_extract` helper under `tools/` retrieves text from PDF files or URLs.
If the pages contain only images, the function can perform OCR using
`pytesseract`. Enable this fallback by passing ``use_ocr=True`` or setting the
``PDF_READER_ENABLE_OCR`` environment variable to ``true``. OCR requires the
Tesseract binary to be installed and accessible on the system.

## **8. Secrets Management**

Store API keys and credentials in a dedicated secrets manager such as
**HashiCorp Vault** or **AWS Secrets Manager**. For local testing, export the
values as environment variables or populate a `.env` file that is sourced before
running the tools. In CI, add the keys as repository secrets and reference them
in workflow steps. See [docs/security.md](docs/security.md) for detailed
guidance.

## **9. Error Logging Middleware**

The orchestration engine supports optional structured error logging. Enable it
by attaching an `ErrorLoggingMiddleware` instance to the engine:

```python
from services.error_logging import ErrorLoggingMiddleware
engine = create_orchestration_engine()
engine.error_logger = ErrorLoggingMiddleware()
```

Set `engine.error_logger = None` to disable logging. The middleware records the
node name, exception, and serialised state for easier debugging.

## **10. Continuous Deployment**

All services are deployed via an automated CD pipeline defined in `.github/workflows/cd.yml`.
The pipeline uses Terraform and Helm configurations under `infra/` to perform
blue–green deployments. The `scripts/deploy.sh` helper script toggles between
`blue` and `green` deployments so the new version is spun up alongside the old
one. Once the new pods are ready, the service selector is patched to shift
traffic with no interruption before the old deployment is removed. While the
blueprint originally called for a rainbow rollout, technical leadership approved
the simpler blue–green approach. See
[docs/research/2025-blue-green-rainbow-analysis.md](docs/research/2025-blue-green-rainbow-analysis.md)
for the detailed rationale. A push to `main` deploys to the `staging`
environment automatically. After verification, an operator can trigger the
`promote-production` job to roll out the same release to production. In case of
issues, `scripts/rollback.sh` reverts the selector to the previous colour.

## **11. Project Roadmap**

This project is being executed in a phased approach to manage complexity and deliver value incrementally. For a complete list of all change requests, see [docs/change_request_ledger.md](docs/change_request_ledger.md).

* **Phase 1: Core Orchestration & Foundational Capabilities**
  * **Objective**: Establish the foundational architecture and a baseline research capability.
  * **Key Deliverables**: LangGraph-based orchestration engine, observability layer, Supervisor and WebResearcher agents, BrowseComp benchmark.
* **Phase 2: Advanced Cognition & Evaluation**
  * **Objective**: Introduce memory and self-correction to improve accuracy and reliability.
  * **Key Deliverables**: LTM service (Episodic Memory), Evaluator agent with self-correction loop, LLM-as-a-Judge pipeline.
* **Phase 3: Dynamic Collaboration & Self-Improvement**
  * **Objective**: Enable complex collaboration and system-level learning.
  * **Key Deliverables**: Dynamic group chat and hierarchical teams, RLAIF loop with Reward Model, Semantic Memory (knowledge graph).
* **Phase 4: Production Hardening & Specialisation**
  * **Objective**: Refine the system for production use, focusing on efficiency and robustness.
  * **Key Deliverables**: Procedural Memory, multi-agent fine-tuning pipeline, mandatory CitationAgent, MAST-based failure testing.

## **12. Contributing**

Contributions are welcome and encouraged! Please follow these steps to contribute:

1. **Fork the repository.**
2. **Create a new branch** for your feature or bug fix: git checkout -b feature/your-feature-name.
3. **Develop your changes.** Ensure your code adheres to the project's style guidelines and that you add appropriate unit tests.
4. **Run all tests** to ensure your changes have not introduced any regressions.
5. **Commit your changes** with a clear and descriptive commit message.
6. **Push your branch** to your fork: git push origin feature/your-feature-name.
7. **Open a Pull Request** against the main branch of this repository.

All pull requests will be automatically validated by the CI pipeline (P1-02), which includes running linters, unit tests, and checking for code coverage. A review from at least one core team member is required for a PR to be merged.
Branch protection rules on `main` enforce these checks so direct pushes are rejected. You can verify the policy by running `scripts/check_branch_protection.py` with a GitHub token.
For instructions on running the pipeline locally and the required 80% coverage threshold, see [docs/ci.md](docs/ci.md).

## Support

If you run into problems or have questions, please open an issue on GitHub.
We actively monitor the repository and will help as soon as possible.

## **13. License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
