# Codex Task Blocks

Tasks in this file can be automatically ingested into `.codex/queue.yml`. Each task is defined in a fenced code block tagged `codex-task` and contains YAML fields.

Example:

```codex-task
id: CODEX-EXAMPLE-01
title: Example task
priority: low
steps:
  - do something
acceptance_criteria:
  - something done
```

## P1-01: Set up mono-repo for agentic system

**Goal:** This task involves the creation of a new Git mono-repository to house all source code and related artifacts for the multi-agent system.

**Tasks:**
- [ ] **Branch Protection:** Configure rules in the version control system (e.g., GitHub, GitLab) to require at least one peer review and successful completion of CI status checks (P1-02) before a pull request can be merged into the main branch.
- [ ] **Pre-commit Hooks:** Use a framework like pre-commit to manage hooks. Recommended hooks include black for standardized code formatting, flake8 or ruff for linting, and isort for organizing imports.

**Acceptance Criteria:**
- [ ] Given a developer has cloned the repository
- [ ] And a branch is protected with a required review rule
- [ ] When the developer attempts to push a commit directly to the protected branch
- [ ] Then the push is rejected by the version control system
- [ ] Given a developer has staged changes containing linting errors
- [ ] When the developer attempts to create a commit
- [ ] Then the pre-commit hook fails and prevents the commit

## P1-02: Implement CI pipeline for automated builds and tests ✅

**Goal:** Implement a CI pipeline using a standard platform (e.

**Tasks:**
- [ ] The pipeline should be optimized for speed by caching dependencies and running jobs in parallel where possible.
- [ ] The CI configuration file (e.g., workflow.yml) must reside within the mono-repo itself, versioning the pipeline alongside the code it tests.

**Acceptance Criteria:**
- [ ] Given a pull request is opened with valid code changes
- [ ] When the CI pipeline completes successfully
- [ ] Then a "pass" status check is visible on the pull request
- [ ] Given a pull request is opened with code changes that break a unit test
- [ ] When the CI pipeline runs the test suite
- [ ] Then the pipeline run is marked as "failed"
- [ ] And a "fail" status check is visible on the pull request

```codex-task
id: P1-02
title: Implement CI pipeline for automated builds and tests
status: done
steps: []
acceptance_criteria: []
```

## P1-03: Implement CD Pipeline for automated deployments

**Goal:** Implement a CD pipeline that automates the deployment of all system services.

**Tasks:**
- [ ] The pipeline must be designed to support zero-downtime deployment strategies. The blueprint specifically mentions "rainbow deployments," which involve deploying the new version alongside the old one and gradually shifting traffic. This is critical for long-running agent processes that cannot be abruptly terminated.
- [ ] All deployment configurations should be managed via infrastructure-as-code (e.g., Terraform, Helm charts) stored within the mono-repo.

**Acceptance Criteria:**
- [ ] Given a pull request has been successfully merged into the main branch
- [ ] When the CD pipeline is triggered
- [ ] Then all system services are automatically deployed to the staging environment
- [ ] Given the staging deployment has been verified and approved
- [ ] When an operator triggers the "promote-to-production" step
- [ ] Then the version from staging is deployed to the production environment

```codex-task
id: P1-03
title: Implement CD Pipeline for automated deployments
status: done
steps: []
acceptance_criteria: []
```

## P1-04: Set up OpenTelemetry collector and exporter

**Goal:** This task involves deploying and configuring an OpenTelemetry (OTel) collector within the system's infrastructure.

**Tasks:**
- [ ] The collector should be deployed as a highly available service.
- [ ] Configuration should include processors for batching data to improve efficiency and adding metadata (e.g., environment, service version) to all telemetry signals.

**Acceptance Criteria:**
- [ ] Given the OpenTelemetry collector is running
- [ ] And a system service is instrumented to send traces
- [ ] When the service performs an action and emits a trace
- [ ] Then the corresponding trace is visible in the configured observability backend

```codex-task
id: P1-04
title: Set up OpenTelemetry collector and exporter
status: done
steps: []
acceptance_criteria: []
```

## P1-05: Define core agent action tracing schema

**Goal:** Define and document a standardized OpenTelemetry tracing schema that will be used across the entire system.

**Tasks:**
- [ ] The schema should be defined in a shared library or document accessible to all development teams.
- [ ] The schema should be versioned to allow for future evolution without breaking existing instrumentation.
- [ ] Consider including metrics like token counts (input\_tokens, output\_tokens) and latency for each LLM call within the trace attributes.

**Acceptance Criteria:**
- [ ] Given the agent action tracing schema is defined
- [ ] When a 'WebResearcher' agent calls the 'web_search' tool with a query
- [ ] Then a trace span is emitted containing attributes for 'agent_id', 'agent_role', 'tool_name', 'tool_input', and 'tool_output'

## P1-06: Implement core Orchestration Engine with graph execution ✅

**Goal:** Implement the core orchestration engine, taking inspiration from the LangGraph framework.

**Tasks:**
- [ ] The blueprint explicitly cites LangGraph as an inspiration. It is highly recommended to use LangGraph as the reference implementation or directly as the underlying library to accelerate development.
- [ ] The engine must be instrumented to emit OpenTelemetry traces (P1-04, P1-05) for every node execution and edge transition, providing deep visibility into the workflow.
- [ ] The engine should expose a method to export the graph structure in a standard format (e.g., DOT), which can be used by tools like Graphviz for visualization and debugging.

**Acceptance Criteria:**
- [ ] Given a graph is defined with NodeA followed by NodeB
- [ ] When the Orchestration Engine's 'execute' method is called with this graph
- [ ] Then NodeA is executed to completion before NodeB is executed

## P1-07: Define and implement the central State object ✅

**Goal:** Define and implement a data structure, referred to as the State object, which will be passed between all nodes in the execution graph.

**Tasks:**
- [ ] Use a library like Pydantic in Python to define the State object's schema, which provides data validation and serialization capabilities out of the box.
- [ ] The State object should be designed to be append-only where possible (e.g., for lists of messages) to provide a clear audit trail of how the state evolved over time.

**Acceptance Criteria:**
- [ ] Given a graph where NodeA modifies the 'State' object
- [ ] When the graph is executed
- [ ] Then the modified 'State' object is passed as input to the subsequent node
- [ ] Given a 'State' object containing data
- [ ] When the object is serialized and then deserialized
- [ ] Then the resulting object is identical to the original

## P1-08: Implement conditional edge router for dynamic workflows ✅

**Goal:** Implement logic within the Orchestration Engine to support conditional edges.

**Tasks:**
- [ ] The router function should be simple and deterministic, containing only the logic to inspect the state and return a string identifier for the next node. All complex business logic should remain within the agent nodes themselves.

**Acceptance Criteria:**
- [ ] Given a graph is defined with a conditional edge routing on the 'status' field
- [ ] And the central State object has 'status' set to 'requires_verification'
- [ ] When the Orchestration Engine executes the current node
- [ ] Then the next node to be executed is the 'Verifier' node

## P1-20: Research optimal graph compilation strategies

**Goal:** This task is a research spike to investigate and compare different strategies for compiling the agent graph into an executable format.

**Tasks:**
- [ ] The research should include small-scale proof-of-concept implementations to gather empirical data on latency and resource usage for both approaches.
- [ ] The final recommendation may be a hybrid approach, where certain well-defined subgraphs can be compiled AOT for performance, while the main orchestrating graph remains dynamic.

**Acceptance Criteria:**
- [ ] Given research has been conducted on graph compilation strategies
- [ ] When a final report is delivered to technical leadership
- [ ] Then the report contains a clear recommendation for the chosen strategy, supported by performance benchmarks and qualitative analysis

```codex-task
id: P1-20
title: Research optimal graph compilation strategies
status: done
steps: []
acceptance_criteria: []
```

## P1-09: Implement Supervisor agent for query analysis

**Goal:** Implement the initial version of the Supervisor agent.

**Tasks:**
- [ ] The Supervisor agent will be implemented as a node within the orchestration graph (P1-06). It will typically be the entry point of the graph.

**Acceptance Criteria:**
- [ ] Given the Supervisor agent is invoked with a user query string
- [ ] When the agent completes its analysis
- [ ] Then it returns a 'State' object with the original query populated in the 'initial_query' field

## P1-10: Implement Supervisor's graph-based planning logic

**Goal:** Enhance the Supervisor agent with the logic to decompose a complex user query into a high-level research plan.

**Tasks:**
- [ ] The prompt for the Supervisor agent must be carefully engineered to instruct the LLM to output the plan in the specific JSON or YAML format that the Orchestration Engine expects for graph definitions.

**Acceptance Criteria:**
- [ ] Given the Supervisor agent receives a query like "Compare the performance of Transformer and LSTM models"
- [ ] When the agent generates a research plan
- [ ] Then the output graph definition contains at least two parallel 'WebResearcher' nodes, one for 'Transformer performance' and one for 'LSTM performance'

## P1-11: Implement WebResearcher agent for information extraction ✅

**Goal:** Implement the WebResearcher agent as a callable node in the execution graph.

**Tasks:**
- [ ] The agent's internal logic should employ reasoning techniques like those described in the blueprint (e.g., "interleaved thinking") to analyze search results and decide which links to follow and scrape.

**Acceptance Criteria:**
- [ ] Given the 'State' object contains a sub-task for the WebResearcher to "find papers on Transformer architecture"
- [ ] When the 'WebResearcher' node is executed
- [ ] Then the agent calls the 'web_search' tool with a relevant query, such as "Transformer architecture academic papers"

## P1-12: Implement WebResearcher's summarization capability ✅

**Goal:** Add a summarization capability to the WebResearcher agent.

**Tasks:**
- [ ] The summarization prompt should instruct the agent to focus on extracting information that is directly relevant to the sub-task it was assigned.

**Acceptance Criteria:**
- [ ] Given the WebResearcher agent has extracted 5,000 words of raw text from a webpage
- [ ] When the agent completes its turn
- [ ] Then a concise summary of that text is added to the 'messages' list in the 'State' object

## P1-13: Create secure Tool Registry service

**Goal:** Create a centralized, standalone service for managing all external tools.

**Tasks:**
- [ ] The registry should expose a simple, stable API (e.g., REST or gRPC) for agents to query.
- [ ] Tool permissions can be defined in a configuration file or a database, mapping agent roles to permitted tool names.

**Acceptance Criteria:**
- [ ] Given the 'WebResearcher' agent has permission to use the 'web_search' tool
- [ ] When the agent requests the 'web_search' tool from the registry
- [ ] Then the registry returns a callable interface for the tool
- [ ] Given the 'WebResearcher' agent does NOT have permission to use the 'code_interpreter' tool
- [ ] When the agent requests the 'code_interpreter' tool from the registry
- [ ] Then the registry returns an 'AccessDeniedError'

## P1-14: Implement Web Search tool wrapper

**Goal:** Create a Web Search tool and register it with the Tool Registry (P1-13).

**Tasks:**
- [ ] API keys and other secrets must be managed securely (e.g., via a secret manager like AWS Secrets Manager or HashiCorp Vault) and not hardcoded in the tool's source code.

**Acceptance Criteria:**
- [ ] Given the Web Search tool is called with the query string "multi-agent systems"
- [ ] When the tool successfully communicates with the external API
- [ ] Then it returns a list of search result objects, where each object contains a 'url', 'title', and 'snippet'

## P1-15: Implement PDF Reader tool wrapper

**Goal:** Create a PDF Reader tool and register it with the Tool Registry (P1-13).

**Tasks:**
- [ ] Use a robust Python library like PyMuPDF or pdfplumber for reliable text extraction.
- [ ] The tool should include error handling for non-existent files, invalid URLs, and scanned (image-based) PDFs that do not contain extractable text.

**Acceptance Criteria:**
- [ ] Given the PDF Reader tool is called with a URL to a valid, text-based PDF document
- [ ] When the tool successfully downloads and parses the document
- [ ] Then it returns a string containing the full text content of the document

## P1-16: Implement HTML Scraper tool wrapper

**Goal:** Create an HTML Scraper tool and register it with the Tool Registry (P1-13).

**Tasks:**
- [ ] Libraries like BeautifulSoup combined with heuristics can be used for basic scraping. For more robust extraction, consider using a library like trafilatura or goose3, which are specifically designed for this purpose.

**Acceptance Criteria:**
- [ ] Given the HTML Scraper tool is called with a URL to a news article page
- [ ] When the tool successfully fetches and parses the HTML
- [ ] Then it returns a string containing only the main body text of the article, excluding navigation links and advertisements

## P1-17: Create initial BrowseComp benchmark dataset

**Goal:** Create the first version of an internal benchmark dataset for automated regression testing.

**Tasks:**
- [ ] The creation of these question-answer pairs requires human creativity and should be a collaborative effort between the Product Management and QA teams.
- [ ] The dataset should be stored in a structured format (e.g., JSON or CSV) and versioned within the mono-repo.

**Acceptance Criteria:**
- [ ] Given the BrowseComp dataset has been created
- [ ] When it is reviewed by the QA and Product teams
- [ ] Then the dataset contains at least 50 unique question-answer pairs
- [ ] And each pair adheres to the "inverted question" and "asymmetry of verification" design principles

## P1-18: Implement Integration-Test Harness for benchmarks

**Goal:** Implement an integration test harness that can programmatically run the entire multi-agent system.

**Tasks:**
- [ ] The test harness should be integrated into the CI pipeline (P1-02) to run on a regular schedule (e.g., nightly) to detect performance regressions quickly.
- [ ] The harness must have a configurable timeout for each question to prevent stalled runs from blocking the entire test suite.

**Acceptance Criteria:**
- [ ] Given the integration test harness is configured with the BrowseComp dataset
- [ ] When the harness is executed
- [ ] Then it runs the system against every question in the dataset
- [ ] And it outputs a summary report containing the overall pass rate and average execution time per question

## P1-19: Create basic unit test framework and coverage goals ✅

**Goal:** Establish the standard unit testing framework for the project (e.

**Tasks:**
- [ ] pytest is the recommended framework for Python due to its rich ecosystem of plugins (e.g., pytest-cov for coverage).
- [ ] The initial coverage target (e.g., 80%) should be realistic but aspirational, and can be adjusted over time. The key is to prevent coverage from decreasing.

**Acceptance Criteria:**
- [ ] Given the code coverage threshold is set to 80%
- [ ] And a developer opens a pull request that lowers the project's coverage to 75%
- [ ] When the CI pipeline runs
- [ ] Then the code coverage check fails and the pipeline is marked as "failed"

## P2-01: Implement LTM Service API for memory operations

**Goal:** Implement the public-facing API for the Long-Term Memory (LTM) service.

**Tasks:**
- [ ] The API design should be granular enough to support different memory types (Episodic, Semantic, Procedural) which will be implemented in later CRs. For example, the /consolidate endpoint might accept a memory\_type parameter.
- [ ] The service must be registered as a tool in the Tool Registry (P1-13) so that access can be managed via RBAC.

**Acceptance Criteria:**
- [ ] Given the LTM service is running
- [ ] When a POST request is sent to the /consolidate endpoint with a valid memory record
- [ ] Then the service returns a 201 Created status
- [ ] Given a memory record has been previously stored
- [ ] When a GET request is sent to the /retrieve endpoint with a relevant query
- [ ] Then the service returns the corresponding memory record

## P2-02: Integrate vector database for Episodic Memory

**Goal:** Provision, configure, and integrate a vector database (e.

**Tasks:**
- [ ] The choice of embedding model is critical and should be evaluated for its performance on the types of text generated by the system.
- [ ] The infrastructure for the vector database should be managed via infrastructure-as-code (P1-01).

**Acceptance Criteria:**
- [ ] Given the LTM service receives a consolidation request for an episodic memory
- [ ] When the service processes the request
- [ ] Then a corresponding vector embedding is created and stored in the vector database

## P2-03: Implement MemoryManager agent for episodic consolidation

**Goal:** Implement a new, specialized agent called the MemoryManager.

**Tasks:**
- [ ] The trigger for the MemoryManager can be implemented as a final, guaranteed node in the orchestration graph or via an event-driven mechanism that listens for "task completed" events.

**Acceptance Criteria:**
- [ ] Given a research task graph successfully terminates
- [ ] When the MemoryManager agent is triggered with the final State object
- [ ] Then the agent makes a call to the LTM's /consolidate endpoint with the formatted episode

## P2-04: Enhance Supervisor to query Episodic LTM for plan templating

**Goal:** Modify the core logic of the Supervisor agent (P1-10).

**Tasks:**
- [ ] The agent's prompt must be updated to include instructions for this new "query LTM first" step.
- [ ] Logic must be included to handle cases where no relevant memories are found, allowing the agent to fall back to generating a plan from scratch.

**Acceptance Criteria:**
- [ ] Given a new query is submitted that is semantically similar to a previously successful task
- [ ] When the Supervisor agent begins planning
- [ ] Then its first action is to call the LTM retrieval endpoint
- [ ] And the new plan it generates shares structural similarities with the retrieved plan

## P2-19: Research memory consolidation and forgetting strategies

**Goal:** Conduct a research spike into advanced strategies for managing the LTM.

**Tasks:**
- [ ] Research should explore concepts from cognitive science, such as spaced repetition and memory decay curves, as potential inspirations for forgetting algorithms.

**Acceptance Criteria:**
- [ ] Given research has been conducted on LTM management
- [ ] When a final report is delivered to technical leadership
- [ ] Then the report proposes at least two distinct algorithms for managing the LTM lifecycle, with a comparative analysis of their trade-offs

## P2-20: Implement basic LTM forgetting mechanism

**Goal:** Implement a basic forgetting mechanism within the LTM service (P2-01).

**Tasks:**
- [ ] The forgetting process should perform a "soft delete" first, marking records for deletion before permanently removing them, to allow for a recovery window.

**Acceptance Criteria:**
- [ ] Given a memory record has a 'last_accessed' timestamp older than N days
- [ ] When the scheduled LTM forgetting job runs
- [ ] Then the specified record is deleted from the LTM

## P2-05: Implement Evaluator agent for critique generation

**Goal:** Implement a new, specialized Evaluator agent.

**Tasks:**
- [ ] The Evaluator's system prompt is critical. It must be instructed to be skeptical, meticulous, and to justify its findings with specific reasons.

**Acceptance Criteria:**
- [ ] Given a piece of text to evaluate is provided as input
- [ ] When the Evaluator agent executes
- [ ] Then it produces a structured critique object containing specific feedback and a pass/fail score

## P2-06: Implement Evaluator's factual accuracy verification logic

**Goal:** Implement logic within the Evaluator agent (P2-05) to perform factual accuracy verification.

**Tasks:**
- [ ] This logic will likely involve using an LLM to perform a series of "question-answering" tasks, where each claim from the summary is turned into a question that is then answered based *only* on the provided source documents.

**Acceptance Criteria:**
- [ ] Given a summary contains a claim that is not present in its source document
- [ ] When the Evaluator agent runs its verification logic
- [ ] Then it flags the specific claim as an "unsupported fact" in its critique output

## P2-07: Implement Evaluator's source quality assessment logic

**Goal:** Implement logic within the Evaluator agent (P2-05) to assess the quality of the sources cited in a research output.

**Tasks:**
- [ ] A blocklist/allowlist of domains can be used to supplement the LLM's heuristic judgment.
- [ ] This assessment can be a criterion in the LLM-as-a-Judge rubric (P2-12) as well.

**Acceptance Criteria:**
- [ ] Given a research output cites only a personal blog as its source
- [ ] When the Evaluator agent runs its assessment
- [ ] Then its critique output includes a low score for the "Source Quality" criterion

## P2-08: Modify Orchestration Engine to support CoSC feedback loop

**Goal:** Modify the Orchestration Engine (P1-06) to enable a Chain of Self-Correction (CoSC) feedback loop.

**Tasks:**
- [ ] The State object (P1-07) must be updated to include the critique from the Evaluator so the generator agent has the necessary feedback for its revision attempt.

**Acceptance Criteria:**
- [ ] Given a graph where a Researcher node is followed by an Evaluator node
- [ ] When the Researcher produces an output and the Evaluator returns a 'fail' status
- [ ] Then the Orchestration Engine routes execution back to the Researcher node for another attempt

## P2-09: Integrate a fact-checking API as an Evaluator tool

**Goal:** Integrate a third-party fact-checking API (e.

**Tasks:**
- [ ] The tool wrapper should handle parsing the API's response into a simple, structured format that the agent can easily interpret (e.g., a JSON object with 'claim', 'rating', 'source\_links').

**Acceptance Criteria:**
- [ ] Given the Evaluator agent is checking a claim about a recent world event
- [ ] When it uses the fact-checking tool
- [ ] Then it receives a credibility rating and supporting links for the claim from the external API

## P2-10: Develop QA tests for the CoSC loop to prevent infinite cycles

**Goal:** Create a specific integration test designed to validate the termination condition of the CoSC loop (P2-08).

**Tasks:**
- [ ] The maximum retry count should be stored in the State object and incremented on each loop. The conditional edge logic (P1-08) must check this counter as part of its routing decision.

**Acceptance Criteria:**
- [ ] Given an Evaluator agent is configured to always fail an output
- [ ] When the CoSC loop is executed
- [ ] Then the loop terminates after a pre-configured maximum number of retries (e.g., 3)

## P2-15: Research synthetic data generation techniques for self-correction

**Goal:** Conduct a research spike to investigate and compare state-of-the-art techniques for synthetically generating training data for self-correction tasks.

**Tasks:**
- [ ] The research should evaluate the trade-offs between different generation methods in terms of cost, quality, and diversity of the generated examples.

**Acceptance Criteria:**
- [ ] Given research has been conducted on synthetic data generation
- [ ] When a final report is delivered to technical leadership
- [ ] Then it recommends a specific, state-of-the-art methodology for generating a high-quality self-correction dataset

## P2-16: Create synthetic dataset of errors and corrections

**Goal:** Using the methodology recommended from the research in P2-15, execute a large-scale data generation process to create a synthetic dataset for fine-tuning self-correction abilities.

**Tasks:**
- [ ] The dataset should cover a diverse range of error types (e.g., factual errors, reasoning fallacies, calculation mistakes, formatting issues).
- [ ] Human review of a subset of the generated data is essential to ensure its quality before use in fine-tuning.

**Acceptance Criteria:**
- [ ] Given the generation process is complete
- [ ] When the dataset is inspected
- [ ] Then it contains at least 1,000 high-quality examples, each with an initial solution, a detailed critique, and a corrected solution

## P2-17: Fine-tune Evaluator agent on the correction dataset

**Goal:** Take the synthetic self-correction dataset generated in P2-16 and use it to fine-tune the underlying language model of the Evaluator agent.

**Tasks:**
- [ ] A holdout portion of the synthetic dataset must be reserved for evaluation to measure the effectiveness of the fine-tuning process.
- [ ] The fine-tuned model should be versioned and stored in a model registry.

**Acceptance Criteria:**
- [ ] Given the fine-tuning process is complete
- [ ] When the newly fine-tuned Evaluator agent is tested on a holdout set of known flaws
- [ ] Then its accuracy at identifying these flaws shows a statistically significant improvement over the base model

## P2-11: Build LLM-as-a-Judge evaluation pipeline

**Goal:** Build an automated pipeline that uses a powerful, state-of-the-art LLM (e.

**Tasks:**
- [ ] The pipeline should be robust to failures in the judge model's API, with retry logic (P4-13) and error handling.
- [ ] The results of the evaluation should be stored in a database or data warehouse for longitudinal analysis of system performance.

**Acceptance Criteria:**
- [ ] Given a generated report and its source documents
- [ ] When the evaluation pipeline is executed
- [ ] Then it outputs a single, valid JSON object containing scores and justifications for each criterion in the rubric

## P2-12: Define comprehensive evaluation rubric as a JSON schema

**Goal:** Define the detailed evaluation rubric that will be used by the LLM-as-a-Judge (P2-11).

**Tasks:**
- [ ] The development of the rubric should be a collaborative effort between Product, QA, and Engineering to ensure it captures the desired qualities of a "good" research report.

**Acceptance Criteria:**
- [ ] Given the JSON schema for the evaluation rubric
- [ ] When it is validated against a schema validator
- [ ] Then it correctly defines all required evaluation criteria, their descriptions, data types, and scoring scales

## P2-13: Curate and label golden dataset of reports for judge calibration

**Goal:** Curate and label a "golden" dataset of research reports.

**Tasks:**
- [ ] At least two human experts should score each report independently to establish inter-annotator agreement and create a more reliable ground truth.

**Acceptance Criteria:**
- [ ] Given the golden dataset has been curated and labeled
- [ ] When it is reviewed by the QA lead
- [ ] Then it contains at least 20 diverse reports with detailed, human-generated scores and justifications for each rubric criterion

## P2-14: Implement judge calibration test suite against golden dataset

**Goal:** Implement a test suite that automatically runs the LLM-as-a-Judge pipeline (P2-11) against every report in the golden dataset (P2-13).

**Tasks:**
- [ ] Cohen's Kappa is a preferred metric as it accounts for agreement that could occur by chance, making it more robust than simple accuracy.
- [ ] This suite should be re-run whenever the judge model or its prompt is changed to ensure reliability is maintained.

**Acceptance Criteria:**
- [ ] Given the calibration suite is run against the golden dataset
- [ ] When it completes
- [ ] Then it outputs a report detailing the agreement score (e.g., kappa > 0.7) between the LLM judge and the human evaluators

## P2-18: Implement a human-in-the-loop breakpoint

**Goal:** Implement a special "breakpoint" node type in the Orchestration Engine (P1-06).

**Tasks:**
- [ ] The UX for the review queue is a critical component of this task. It should clearly present the current state and provide a simple mechanism for the human to approve, reject, or modify the state before resuming execution.

**Acceptance Criteria:**
- [ ] Given a graph contains a 'human_in_the_loop_breakpoint' node
- [ ] When the Orchestration Engine executes that node
- [ ] Then the graph execution state is paused
- [ ] And an alert is sent to the human review queue with the current State object

## P3-01: Implement GroupChatManager for agent collaboration ✅

**Goal:** Implement a new special node type in the Orchestration Engine (P1-06) called the GroupChatManager.

**Tasks:**
- [ ] The GroupChatManager can implement various turn-taking policies, such as a simple round-robin or a more sophisticated policy where an LLM decides which agent should speak next based on the conversation history.

**Acceptance Criteria:**
- [ ] Given a group chat is initiated with Agent A and Agent B
- [ ] When Agent A sends a message into the chat
- [ ] Then Agent B receives that message in its next turn within the chat

## P3-02: Define agent message passing protocol for group chat

**Goal:** Define and implement a structured, formal protocol for messages passed within the group chat framework (P3-01).

**Tasks:**
- [ ] The base agent prompt should be updated to instruct agents on how to construct and interpret messages according to this protocol.

**Acceptance Criteria:**
- [ ] Given the message protocol is defined
- [ ] When Agent A sends a message with type 'question' addressed specifically to Agent B
- [ ] Then the recipient agent's context is updated to reflect the directed question from Agent A

## P3-03: Implement hierarchical subgraph spawning for agent teams

**Goal:** Enhance the Orchestration Engine (P1-06) and the Supervisor agent (P1-10) to support the concept of hierarchical subgraphs.

**Tasks:**
- [ ] This feature requires careful state management to pass context down to the subgraph and return the result back up to the parent graph's State object.

**Acceptance Criteria:**
- [ ] Given the Supervisor's plan includes a subgraph node for a complex sub-task
- [ ] When the Orchestration Engine executes that node
- [ ] Then a new, nested instance of the orchestration engine is created and executed for the subgraph
- [ ] And the main graph pauses until the subgraph reports its final result

## P3-04: Implement a shared collaborative scratchpad

**Goal:** Add a new field, scratchpad, to the central State object (P1-07).

**Tasks:**
- [ ] The scratchpad is particularly useful for sharing large data artifacts, like the full text from a scraped webpage, without cluttering the formal message history.

**Acceptance Criteria:**
- [ ] Given two agents are collaborating in a group chat
- [ ] When Agent A writes its intermediate findings to the scratchpad field in the State object
- [ ] Then Agent B can read the updated content from the scratchpad on its next turn

## P3-05: Develop QA tests for inter-agent communication protocols

**Goal:** Create a suite of integration tests designed to validate the robustness and resilience of the inter-agent communication protocols defined in P3-02.

**Tasks:**
- [ ] These tests will likely require mocking the communication layer to inject faults and simulate failure conditions.

**Acceptance Criteria:**
- [ ] Given a test scenario is configured to simulate a lost message between two agents
- [ ] When the test runs
- [ ] Then it verifies that the sending agent's retry logic is correctly triggered after a timeout

## P3-20: Research emergent communication protocols in group chat

**Goal:** Investigate the potential for enabling emergent communication protocols within the group chat framework (P3-01).

**Tasks:**
- [ ] The research report should consider the trade-offs between fully emergent protocols and guided evolution, where agents learn within the constraints of a base protocol.

**Acceptance Criteria:**
- [ ] Given the research phase is complete
- [ ] When a report is delivered to technical leadership
- [ ] Then it includes a detailed proof-of-concept design for an RL environment to train and evaluate emergent communication protocols

## P3-21: Develop QA tests for race conditions in group chat

**Goal:** Develop a specific suite of integration tests to identify and handle concurrency issues within the GroupChatManager (P3-01).

**Tasks:**
- [ ] These tests can be challenging to write and may require specialized libraries for simulating concurrent execution.

**Acceptance Criteria:**
- [ ] Given a test where two agents attempt to write to the same field in the shared scratchpad simultaneously
- [ ] When the test runs
- [ ] Then it verifies that a locking mechanism or an atomic update operation prevents data corruption

## P3-06: Implement Reward Model training pipeline

**Goal:** Implement an MLOps pipeline to train a Reward Model.

**Tasks:**
- [ ] The execution trace used for training should include not just the final output, but also key intermediate steps, agent actions, and collaboration metrics (P3-09) to provide rich features for the model.
- [ ] This pipeline should be automated to run periodically as new evaluation data becomes available.

**Acceptance Criteria:**
- [ ] Given a dataset of 1,000+ evaluated research task trajectories
- [ ] When the training pipeline is run
- [ ] Then it outputs a versioned, trained Reward Model artifact to the model registry

## P3-07: Integrate a PPO library for RLAIF loop

**Goal:** Integrate a standard, well-supported reinforcement learning library (e.

**Tasks:**
- [ ] TRL (Transformer Reinforcement Learning) is a strong candidate as it is specifically designed for fine-tuning transformer-based language models.

**Acceptance Criteria:**
- [ ] Given a policy model, an agent trajectory, and rewards from the Reward Model
- [ ] When the PPO algorithm is run for one step
- [ ] Then it computes and applies gradients to the policy model's weights

## P3-08: Connect RLAIF loop to update Supervisor's policy

**Goal:** Connect the PPO-based RLAIF loop (P3-07) to the Supervisor agent's policy model (P1-10).

**Tasks:**
- [ ] This process requires careful management of the policy model, the value model (used by PPO), and the reward model, likely all managed within a central model registry.

**Acceptance Criteria:**
- [ ] Given the RLAIF loop has run for several epochs on Supervisor planning data
- [ ] When the Supervisor is given a task it previously performed poorly on
- [ ] Then its new plan is measurably different and aligns better with high-reward strategies

## P3-09: Log system and collaboration metrics for the Reward Model

**Goal:** Instrument the Orchestration Engine (P1-06) and the GroupChatManager (P3-01) to log detailed system and collaboration metrics as part of the execution trace defined by the tracing schema (P1-05).

**Tasks:**
- [ ] These metrics should be added as attributes to the root span of the task's trace in OpenTelemetry for easy correlation.

**Acceptance Criteria:**
- [ ] Given a group chat task completes
- [ ] When the execution trace for that task is examined
- [ ] Then it contains structured metrics like 'total_messages_sent', 'average_message_latency', and 'action_advancement_rate'

## P3-10: Research SCoRe-based reward shaping for self-correction

**Goal:** Conduct a research spike into reward shaping techniques inspired by the SCoRe (Self-Correction via Reinforcement Learning) framework.

**Tasks:**
- [ ] The proposed reward function might, for example, provide a large positive reward only if the initial output was 'fail' and the revised output is 'pass'.

**Acceptance Criteria:**
- [ ] Given the research phase is complete
- [ ] When a report is delivered to technical leadership
- [ ] Then it proposes a specific, mathematically defined reward function to be used for training self-correction behavior via RLAIF

## P3-11: Implement CodeResearcher agent with secure tool use

**Goal:** Implement a new CodeResearcher agent.

**Tasks:**
- [ ] The agent's prompt should be tailored for a senior software engineer persona, instructing it to think about test cases, edge cases, and debugging strategies.

**Acceptance Criteria:**
- [ ] Given a Python function with a known bug and a task to identify it
- [ ] When the CodeResearcher agent executes
- [ ] Then it calls the code interpreter tool with the function's code and relevant inputs to trigger the bug

## P3-12: Provision secure code interpreter sandbox environment

**Goal:** Provision and configure a secure, isolated sandbox environment for use by the Code Interpreter tool (P3-18).

**Tasks:**
- [ ] Firecracker is an excellent choice for this as it provides VM-level security with container-like speed and efficiency.

**Acceptance Criteria:**
- [ ] Given code is being executed within the sandbox environment
- [ ] When that code attempts to make an outbound network call
- [ ] Then the operation is blocked by the sandbox and a security error is returned to the agent

## P3-13: Implement Planner agent base class

**Goal:** Implement the base class for a Planner agent.

**Tasks:**
- [ ] The Planner and Supervisor represent two different philosophies of planning: optimization vs. generative reasoning. The system should be flexible enough to use either, depending on the nature of the task.

**Acceptance Criteria:**
- [ ] Given a research query is provided
- [ ] When the Planner agent is invoked
- [ ] Then it produces a structured plan object that can be executed by the Orchestration Engine

## P3-14: Implement greedy algorithm for task allocation in Planner

**Goal:** Implement a greedy algorithm within the Planner agent (P3-13) for task allocation.

**Tasks:**
- [ ] Agent "skill" can be represented as metadata or even as embeddings, allowing the planner to calculate a similarity score between the task description and the agent's profile.

**Acceptance Criteria:**
- [ ] Given a list of pending tasks and a pool of agents with different skills
- [ ] When the Planner agent runs its allocation algorithm
- [ ] Then each task is assigned to the agent with the highest skill match for that task

## P3-18: Implement a basic Code Interpreter tool

**Goal:** Create and register a Code Interpreter tool with the Tool Registry (P1-13).

**Tasks:**
- [ ] The tool must enforce strict timeouts to prevent long-running or infinite-looping code from consuming resources.

**Acceptance Criteria:**
- [ ] Given the tool receives the code string 'print("hello world")'
- [ ] When the tool executes the code in the sandbox
- [ ] Then it returns a result object where the 'stdout' field is equal to "hello world"

## P3-19: Implement a GitHub Search API tool

**Goal:** Create and register a GitHub Search tool with the Tool Registry (P1-13).

**Tasks:**
- [ ] The tool should respect the API rate limits of the GitHub API and implement appropriate backoff logic.

**Acceptance Criteria:**
- [ ] Given a query for a specific open-source library
- [ ] When the GitHub Search tool is called with the query
- [ ] Then it returns a list of relevant repository URLs and descriptions

## P3-15: Integrate graph database for Semantic LTM

**Goal:** Provision, configure, and integrate a graph database (e.

**Tasks:**
- [ ] The choice of graph schema (e.g., property graph model) is a key design decision that will affect query performance and flexibility.

**Acceptance Criteria:**
- [ ] Given the LTM service receives a request to store a fact (e.g., subject, predicate, object)
- [ ] When it processes the request for the Semantic Memory module
- [ ] Then a corresponding node and relationship are created in the graph database

## P3-16: Enhance MemoryManager to extract entities for knowledge graph

**Goal:** Enhance the MemoryManager agent (P2-03) with Named Entity Recognition (NER) and Relation Extraction capabilities.

**Tasks:**
- [ ] This capability will require a sophisticated LLM prompt that instructs the model to act as a knowledge extraction engine and to output the results in a structured format (e.g., a list of subject-predicate-object triples).

**Acceptance Criteria:**
- [ ] Given a verified report contains the sentence "Apple acquired NeXT in 1997"
- [ ] When the MemoryManager agent processes this report
- [ ] Then it adds nodes for 'Apple' and 'NeXT' with an 'ACQUIRED' relationship (with a 'year' property of 1997) to the knowledge graph

## P3-17: Implement agent query path for Semantic LTM

**Goal:** Modify the base logic of all information-seeking agents (e.

**Tasks:**
- [ ] This can be implemented by adding a "knowledge graph search" tool to the agents' permitted tool list and instructing them in their system prompts to prefer it for factual queries.

**Acceptance Criteria:**
- [ ] Given an agent needs to find a specific fact, like "the capital of France"
- [ ] When the agent executes its turn
- [ ] Then its first action is to query the Semantic LTM service before attempting an external web search

## P4-01: Implement Procedural Memory module in LTM Service

**Goal:** Implement the Procedural Memory module within the LTM service (P2-01).

**Tasks:**
- [ ] Procedures should be stored with metadata describing the task goal they achieve, which can be used for effective retrieval.

**Acceptance Criteria:**
- [ ] Given the LTM service receives a request to store a new procedure
- [ ] When it processes the request
- [ ] Then the sequence of actions is successfully saved in the procedural memory store

## P4-02: Instrument agents to identify and store successful tool sequences

**Goal:** Instrument the base agent class to log the sequence of tool calls it makes during a task.

**Tasks:**
- [ ] The generalization logic is key. It should try to replace specific arguments with placeholders to make the procedure more broadly applicable. For example, web\_search(query="Transformer architecture") might be generalized to web\_search(query=$topic).

**Acceptance Criteria:**
- [ ] Given an agent successfully uses a sequence of three tools to complete a task
- [ ] When the task finishes successfully
- [ ] Then a new procedure containing those three tool calls is sent to the LTM service for storage

## P4-03: Enhance agents to query and execute stored procedures

**Goal:** Modify the agent's decision-making logic to query Procedural Memory at the start of a task.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given a new task is assigned to an agent that matches a stored procedure in LTM
- [ ] When the agent begins its turn
- [ ] Then it retrieves and executes the procedure's action sequence directly without further reasoning

## P4-04: Add LTM hit-rate metrics to observability dashboard

**Goal:** Add widgets to the main observability dashboard to track LTM hit rates for each memory type (Episodic, Semantic, Procedural).

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given the system is running and processing tasks
- [ ] When an operator views the main observability dashboard
- [ ] Then they can see a time-series graph displaying the hit rate for each LTM type

## P4-05: Research RAG vs fine-tuning for procedural memory recall

**Goal:** Conduct a research spike to compare two approaches for teaching agents to use procedural memory: Retrieval-Augmented Generation (RAG) where procedures are injected into the context, versus fine-tuning the agent's model to learn procedures implicitly.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given the research spike is complete
- [ ] When a report is delivered to technical leadership
- [ ] Then it provides a data-backed recommendation on whether to use RAG, fine-tuning, or a hybrid approach for procedural memory

## P4-06: Build MLOps pipeline for parallel multi-agent fine-tuning

**Goal:** Build an MLOps pipeline to support multi-agent fine-tuning.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given a pool of five distinct WebResearcher agents
- [ ] When the multi-agent fine-tuning pipeline is executed
- [ ] Then it triggers five separate fine-tuning jobs, one for each agent, using only that agent's collected data

## P4-07: Modify Supervisor to select agents from a diverse, specialized pool

**Goal:** Modify the Supervisor (or Planner) agent's task allocation logic.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given a task requires analyzing a 10-K report
- [ ] And a pool of WebResearcher agents contains one that has specialized in financial topics
- [ ] When the Supervisor allocates the task
- [ ] Then it selects the financial specialist agent for the job

## P4-08: Develop agent policy divergence and specialization metrics

**Goal:** Develop a set of metrics to quantify the diversity of policies within a pool of specialized agents.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given the multi-agent fine-tuning pipeline has run over several cycles
- [ ] When the policy divergence metrics are calculated
- [ ] Then the resulting report shows a measurable increase in policy divergence among the agent pool over time

## P4-09: Implement CitationAgent with source-claim matching logic

**Goal:** Implement the CitationAgent.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given a sentence in a final report and a set of source documents
- [ ] When the CitationAgent runs its matching logic
- [ ] Then it correctly identifies and returns the specific source document and passage that supports the sentence

## P4-10: Implement citation formatting based on specified styles

**Goal:** Enhance the CitationAgent to format the matched source-claim pairs into proper citations.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given a matched source-claim pair and a specified style of 'APA'
- [ ] When the CitationAgent formats the citation
- [ ] Then the output string adheres to the APA citation format rules

## P4-11: Integrate CitationAgent as a final, mandatory graph node

**Goal:** Modify the Supervisor's planning logic to ensure that the CitationAgent is always included as one of the final nodes in any research graph.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given any research plan generated by the Supervisor
- [ ] When the graph definition is inspected
- [ ] Then it contains a CitationAgent node that is guaranteed to run before the final termination node

## P4-12: Implement state checkpointing for robust fault recovery

**Goal:** Implement robust state checkpointing in the Orchestration Engine.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given a graph execution fails at step N due to a system crash
- [ ] When the task is manually or automatically resumed
- [ ] Then the Orchestration Engine loads the state from the last successful checkpoint (N-1) and restarts execution from step N

## P4-13: Implement exponential backoff and retry logic in tool calls

**Goal:** Add exponential backoff and retry logic to the wrappers for all external tool calls.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given a tool call fails with a transient error code (e.g., 503 Service Unavailable)
- [ ] When the agent's logic proceeds
- [ ] Then it automatically retries the tool call after a short, exponentially increasing delay

## P4-14: Develop MAST test for Step Repetition (FM-1.3)

**Goal:** Create an integration test based on the MAST taxonomy to detect unnecessary step repetition (FM-1.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given a task has been successfully solved and stored in Episodic LTM
- [ ] When a nearly identical task is submitted
- [ ] Then the execution trace shows a hit on Episodic LTM and a significantly shorter workflow with fewer tool calls

## P4-15: Develop MAST test for Information Withholding (FM-2.4)

**Goal:** Create an integration test to provoke Information Withholding (FM-2.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given Agent A is collaborating with Agent B in a group chat
- [ ] And Agent A possesses a critical fact required to solve the task
- [ ] When the collaborative task is executed
- [ ] Then the final output produced by Agent B correctly incorporates the critical fact from Agent A

## P4-16: Develop MAST test for Incorrect Verification (FM-3.3)

**Goal:** Create an integration test for Incorrect Verification (FM-3.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given a research task where the primary source contains a known factual error
- [ ] When the Evaluator agent critiques the research output based on that source
- [ ] Then its critique explicitly identifies and flags the specific factual error

## P4-17: Expand Tool Registry with specialized database connectors

**Goal:** Expand the Tool Registry with a set of specialized and robust connectors for querying common structured databases (e.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given a SQL Query tool is registered in the Tool Registry
- [ ] When an authorized agent calls it with a valid SQL query
- [ ] Then it receives the query results in a structured format (e.g., JSON)

## P4-18: Research spatio-temporal memory structures

**Goal:** Conduct research into advanced memory structures, specifically spatio-temporal memory.

**Tasks:**
- [ ] TBD

**Acceptance Criteria:**
- [ ] Given the research phase is complete
- [ ] When a report is delivered to technical leadership
- [ ] Then it proposes a detailed data model and API design for a spatio-temporal memory module capable of versioning facts over time

```codex-task
id: P5-01
title: Implement System Monitoring service
steps: []
acceptance_criteria: []
```

```codex-task
id: P5-02
title: Docker-based OTel collector service

title: Add rollback support for CD pipeline
steps: []
acceptance_criteria: []
```

```codex-task
id: P5-03
title: Add graph compilation benchmark script
steps: []
acceptance_criteria: []
```


