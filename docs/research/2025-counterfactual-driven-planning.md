
# **From Synthesis to Discovery: A Research Blueprint for Counterfactual-Driven Planning in Multi-Agent Systems**

## **Part I: The Causal Imperative in Autonomous Research**

This initial section establishes the core thesis: to achieve genuine autonomous discovery, a research agent must move beyond correlation-based planning and embrace causal reasoning. It frames the proposed work not as an incremental improvement but as a fundamental shift in the agent's cognitive capabilities, grounded in established causal theory.

### **1.1 The Limitations of Associational Planning: Beyond Episodic Memory**

The multi-agent research system, as architected, demonstrates high efficiency in tasks that can be decomposed and parallelized.1 A central component of its planning process is the

Supervisor agent, which formulates a high-level research strategy. A key mechanism for this is its ability to query a long-term Episodic Memory. This memory module stores records of entire past research tasks, including the initial query, the final plan, and the resulting report.1 When faced with a new query, the

Supervisor can perform a semantic search over this episodic memory to find similar past tasks and reuse successful plans and strategies.

While this approach is highly effective for solving problems that are similar to those encountered previously, it represents an "exploitation-heavy" strategy. The system excels at refining and executing known pathways to information. However, this very efficiency creates a fundamental bottleneck for true innovation. The system's planning is architecturally constrained to confirming known information paths and is ill-equipped to systematically discover novel research avenues or, more importantly, to challenge the foundational assumptions within a given research domain.1 Its reasoning is fundamentally associative, identifying patterns of success in past data but lacking a deeper understanding of

*why* those patterns hold.

To contextualize this limitation, it is useful to employ Judea Pearl's "Ladder of Causation," a conceptual framework that delineates three distinct levels of cognitive ability.2

1. **Rung 1: Association.** This level involves seeing and observing, dealing with purely statistical relationships. It answers questions of the form, "What if I see...?" or "What does a symptom tell me about a disease?". The current system, by retrieving plans based on correlations between query types and successful outcomes, operates exclusively on this rung.  
2. **Rung 2: Intervention.** This level involves doing or intervening, which allows for predicting the effects of deliberate actions. It answers questions like, "What if I do...?" or "What will happen if I take this drug?". This is the level of controlled experiments.  
3. **Rung 3: Counterfactuals.** This is the highest level of causal reasoning, involving imagining, retrospection, and understanding. It answers "what if" questions about alternative pasts, such as, "What if I had acted differently?" or "Was it the aspirin that stopped my headache?".2

The proposed research is a concrete plan to build the machinery necessary for the agent system to ascend this ladder. The objective is to move from the associational capabilities of Rung 1 to the imaginative, hypothesis-generating power of Rung 3\. This transition is not an incremental improvement; it requires a new class of cognitive tools capable of representing and reasoning about the causal mechanisms that underpin a domain. Simply improving the retrieval algorithms for Episodic Memory would only make the system a more efficient associational engine; it would not grant it the ability to innovate.

### **1.2 Structural Causal Models (SCMs) as the Language of "Why"**

To enable an agent to climb the Ladder of Causation, it must be equipped with a language for representing not just correlations, but causal relationships. The most rigorous and widely adopted framework for this purpose is the Structural Causal Model (SCM).2 An SCM is a mathematical framework used to represent and analyze causal relationships between variables, moving beyond the purely statistical descriptions of traditional machine learning models.6

An SCM is formally defined by three components 8:

1. **A Causal Graph:** A set of variables is represented as nodes in a Directed Acyclic Graph (DAG), where a directed edge from variable X to variable Y (X→Y) signifies that X is a direct cause of Y.6  
2. **Structural Equations:** A set of functions, Xi​:=fi​(PAi​,Ui​), where each function fi​ specifies the value of a variable Xi​ based on the values of its direct causes (its parents in the graph, PAi​) and an unobserved, exogenous error term Ui​.5 These equations describe the autonomous physical mechanisms of the data-generating process.  
3. **A Distribution over Exogenous Variables:** A probability distribution P(U) over the unobserved error terms, which represent all external factors and stochasticity not explicitly modeled in the graph.

The essential power of an SCM lies in its ability to encode causal mechanisms, not just statistical dependencies.6 While a standard statistical model might represent the relationship between variables as a joint probability distribution

P(X,Y,Z), an SCM provides a non-parametric representation of the mechanisms themselves. This distinction is critical. It is the explicit modeling of these mechanisms that allows the system to predict the effects of interventions (by modifying a specific structural equation) and to evaluate counterfactuals (by reasoning about the exogenous variables), capabilities that are impossible to achieve from purely associational data without strong, untestable assumptions.8

### **1.3 Counterfactuals: The Engine of Hypothesis Generation**

Counterfactual reasoning is the ability to consider "what if" scenarios by evaluating alternative possibilities that contradict observed facts.15 As articulated by researchers at Stanford HAI, it is a key process humans use to make causal judgments, going beyond the here and now to imagine how things could have happened differently.18 In the context of AI, counterfactuals are most often used for explainability—for example, to explain a model's decision by showing the smallest change in inputs that would have led to a different outcome (e.g., "Your loan was denied, but if your income had been $10,000 higher, it would have been approved.").15

This research proposes to repurpose this powerful concept. Instead of using counterfactuals for post-hoc explanation, the agent system will use them proactively for *exploration and hypothesis generation*. By systematically asking counterfactual questions about the established knowledge in a domain, the system can generate novel research avenues. A query like, "What if the prevailing assumption that gene A causes disease B is wrong?" is no longer a philosophical question but a computable query that can seed a new, exploratory research plan. This aligns with emerging frameworks for automated hypothesis generation that leverage LLMs and causal structures to uncover new insights from vast bodies of literature.19

The computation of counterfactuals from an SCM is a well-defined, three-step procedure, ensuring that the reasoning is principled and not arbitrary speculation 5:

1. **Abduction:** Given a factual observation (e.g., in the real world, X=x and Y=y), use the SCM to infer the posterior probability distribution of the unobserved exogenous variables U. This step uses the evidence to determine the specific context of the "world" in which the observation occurred.  
2. **Action:** Modify the original SCM, M, by performing a hypothetical intervention. This involves replacing the structural equation for the counterfactual antecedent with a new value (e.g., setting X to a new value x′). This creates a new, "mutilated" model, Mx′​.  
3. **Prediction:** Use the mutilated model Mx′​ and the inferred distribution of the exogenous variables from the abduction step to compute the probability of the outcome variable Y in this counterfactual world.

By equipping the Planner agent with a module capable of executing this procedure, the system transitions from a highly efficient information synthesizer to a genuine research partner, capable of imagining alternative realities and designing experiments to test them.

## **Part II: Architecting the Causal Reasoning Module**

This section details the technical architecture of the proposed Causal Reasoning Module and its integration into the existing multi-agent system. The design prioritizes modularity, ensuring that the complex logic of causal reasoning is encapsulated as a specialized service, which can be developed, tested, and improved independently while providing a clear interface to the rest of the system.

### **2.1 System Integration: A Causal Reasoning Service for the Planner Agent**

The Causal Reasoning Module will be implemented as a distinct, stateful service, housed within the "Cognitive Modules" layer of the system architecture, alongside the Tool Registry and the Long-Term Memory (LTM) Service.1 This architectural choice is deliberate; it treats causal reasoning as a fundamental cognitive capability, analogous to memory or tool use, rather than an ad-hoc feature bolted onto a single agent. The module will expose a well-defined API that can be queried by the

Planner agent.

This design introduces a critical modification to the agent's core planning cycle. In the existing system, the Planner's primary strategy is to query the Episodic Memory to retrieve and adapt previously successful plans.1 The augmented workflow will introduce a new decision point: the

Planner can now choose between **exploiting** known solutions from Episodic Memory or **exploring** novel research avenues by querying the Causal Reasoning Module. This establishes a formal exploration-exploitation dynamic within the planning phase itself, a hallmark of sophisticated decision-making systems.

This architecture draws inspiration from the emerging paradigm of "Causal Agents".23 Research in this area recognizes that LLMs, while possessing vast associational knowledge, struggle with the formalisms of causal theory and reasoning over structured data.23 The solution is to equip the LLM agent with external, specialized "causal tools." Our Causal Reasoning Module functions precisely as such a tool, offloading the heavy lifting of causal discovery and inference and allowing the LLM-based

Planner to operate at a higher level of abstraction.

### **2.2 Component 1: The Causal Discovery Engine**

The first core component of the module is the Causal Discovery Engine. Its sole purpose is to construct and maintain a probabilistic Structural Causal Model (SCM) of the research domain.

* **Input:** The engine's primary data source is the system's Semantic Memory. This memory layer is implemented as a knowledge graph (KG) that stores verified facts, entities, and their relationships, which have been extracted and consolidated from high-quality outputs of previous research tasks.1 This KG serves as a rich, structured representation of the domain's established knowledge.  
* **Process:** The engine will employ a suite of causal discovery algorithms, detailed in Part III, to learn the structure and parameters of an SCM from the KG. This is not a static, one-time process. The engine will be designed to update the causal model incrementally as the Semantic Memory is enriched with new information from subsequent research tasks, allowing the system's "worldview" to evolve.  
* **Output:** The engine's output is a complete, probabilistic SCM. This includes the causal DAG, which represents the system's current "theory" of how variables in the domain influence one another, and the associated structural equations that quantify these relationships.

### **2.3 Component 2: The Counterfactual Generation Engine**

The second core component is the Counterfactual Generation Engine, which operationalizes the causal model to answer "what if" questions posed by the Planner.

* **Input:** This engine takes two inputs: the current SCM from the Causal Discovery Engine and a formal counterfactual query from the Planner. A query might take the form: "Given the observed evidence Z, what would be the probability distribution of outcome Y if variable X had been value x′ instead of its observed value x?"  
* **Process:** The engine implements the formal, three-step abduction-action-prediction algorithm for computing counterfactuals.5 By executing this procedure, it can simulate the state of the domain under a hypothetical condition that contradicts the known facts stored in the  
  Semantic Memory.  
* **Output:** The engine returns a probabilistic description of the counterfactual outcome. This is not a single value but a probability distribution over the relevant variables, which the Planner will then use to formulate a new, exploratory research plan.

### **2.4 Interaction Protocols and Research Subgraph Generation**

The integration of this module necessitates new interaction protocols between the Planner and the system's cognitive architecture.

1. **Query Formulation:** The Planner agent will be prompted with new directives to leverage this capability. It will be tasked with analyzing the current research context and the causal DAG to identify high-leverage points for counterfactual inquiry. For example, it could identify nodes with high centrality in the causal graph or long-standing assumptions in the field (represented as strong, unquestioned edges) as prime candidates for being challenged.  
2. **From Counterfactual to Plan:** The output from the Counterfactual Generation Engine is a description of an alternative world. The Planner's next task is to translate this abstract outcome into a concrete, executable research plan. For instance, if the counterfactual analysis suggests that, in a world where the established cause A→B is severed, an alternative variable C becomes a likely cause of B, the Planner will generate a new research hypothesis: "Investigate the potential causal link C→B."  
3. **Subgraph Instantiation:** This hypothesis is then compiled into a new research subgraph within the system's LangGraph-based architecture.1 This subgraph would contain a team of agents, such as  
   WebResearcher and DataAnalyzer, with specific objectives: "Find academic literature supporting or refuting a link between C and B" and "Analyze available datasets for a statistically significant correlation between C and B, while controlling for A." This exploratory subgraph is then added to the main research graph for execution in parallel with other, potentially more conventional, research threads.

This architecture effectively creates a "Causal World Model" for the research domain. This concept, explored in recent work on bridging LLMs and causality, posits that an agent's planning and reasoning can be dramatically improved if it can interact with a learned, causal simulator of its environment.26 The

Planner agent is no longer limited to its own parametric knowledge or the specific experiences stored in Episodic Memory. Instead, it can perform "look-ahead" simulations by querying the Causal Reasoning Module. This allows it to evaluate multiple, hypothetical futures based on the domain's underlying causal dynamics before committing resources to a specific research path. This reframes the proposed work from merely adding a new feature to constructing a learned, interactive causal world model, placing it at a major frontier of AI research and strengthening both its theoretical and practical justification.

## **Part III: Causal Discovery from the Semantic Knowledge Graph**

This section provides a technical deep-dive into the methodology for constructing the Structural Causal Model (SCM) from the Semantic Memory. This is one of the most technically novel and challenging aspects of the proposal, as it involves adapting and synthesizing state-of-the-art techniques to a unique data substrate.

### **3.1 The Semantic Memory as a Causal Substrate**

The foundational premise of this work is that the system's Semantic Memory, a knowledge graph (KG) storing verified facts and relationships, can be treated as a rich source of observational data for discovering the causal structure of a scientific domain.1 This approach aligns with the emerging field of

**knowledge-based causal discovery**, which seeks to infer causal relationships by reasoning over the semantic metadata of variables (e.g., their names, textual descriptions, and connections within a KG) rather than relying on traditional numerical datasets.32

This is a critical choice because it allows the system to leverage the vast, structured, and context-rich information that it has already curated, turning its own knowledge base into a substrate for deeper reasoning. LLMs alone, while powerful, often produce unstable and inconsistent results when tasked with causal inference directly, as they lack a grounding in a structured causal model.25 By integrating the KG, we provide this necessary grounding.

### **3.2 A Hybrid Methodology for Causal Structure Learning**

Given the complexity of the task, a single algorithm is unlikely to suffice. Therefore, a multi-stage, hybrid methodology is proposed. This approach combines the strengths of KGs (structure), LLMs (semantic understanding), and traditional machine learning (ranking and refinement), drawing inspiration from cutting-edge research frameworks like "Paths to Causality" 34 and related work on automating hypothesis generation.21

The process for discovering a causal link between any two concepts (variables) in the KG will proceed as follows:

1. **Step 1: Informative Subgraph Extraction.** The process begins by identifying potentially relevant contextual information from the KG. For a given pair of variables, (A,B), the system will query the KG to extract connecting paths and small subgraphs. These subgraphs, often defined by metapaths (sequences of node and edge types), represent the existing knowledge pathways that link A and B.34 For example, a path might be  
   Gene \-\> Regulates \-\> Protein \-\> InteractsWith \-\> Disease.  
2. **Step 2: LLM-Powered Relevance Estimation.** Not all extracted subgraphs are equally informative. A powerful LLM will be used as a first-pass filter. For each candidate subgraph, the LLM will be prompted to provide a preliminary estimate of its relevance for inferring a causal relationship between the original variable pair, (A,B).35 This leverages the LLM's broad, pre-trained knowledge to quickly assess the semantic plausibility of the connection.  
3. **Step 3: Learning-to-Rank (LTR) for Subgraph Refinement.** The relevance scores generated by the LLM are then used as training data for a more specialized **Learning-to-Rank (LTR)** model. This step reframes the problem as a classic information retrieval task: the variable pair (A,B) is the "query," and the extracted subgraphs are the "documents" to be ranked in order of relevance.34 Training a dedicated LTR model has been shown to consistently outperform general-purpose LLMs at this ranking task, as it can learn the specific features of a subgraph that are most predictive of a true causal link.  
4. **Step 4: LLM-Based Causal Inference with KG-as-Prompt.** The top-k most informative subgraphs, as ranked by the LTR model, are selected. These subgraphs are then "verbalized"—converted into a sequential text format—and injected directly into a zero-shot prompt for a state-of-the-art LLM. The final prompt will include the instruction, the original textual context (if any), and the verbalized evidence from the KG. The LLM is then tasked with making the final inference: does A cause B, does B cause A, is there a confounder, or is there no direct causal relationship?.34 This "KG Structure as Prompt" approach grounds the LLM's final reasoning in the most relevant structural information available.  
5. **Step 5: SCM Construction.** The pairwise causal relationships discovered through this process are aggregated to construct a global Directed Acyclic Graph (DAG) for the entire domain. Once the DAG structure is established, the structural equations of the SCM can be estimated. Initially, these can be simple linear models. For greater expressiveness, they can be modeled using more complex, non-linear functions learned by neural networks, following approaches from the Causal Deep Learning literature.2

### **3.3 Addressing Key Challenges**

This ambitious approach must acknowledge and address several fundamental challenges:

* **Discovery from Observational Data:** It is a well-known impossibility result that the true causal DAG cannot be uniquely identified from purely observational data without making strong, untestable assumptions.2 Multiple DAGs can be statistically indistinguishable (forming a Markov equivalence class). Therefore, the output of this process must be treated as a  
  *hypothesized* causal graph—the system's best current theory—not an infallible ground truth. The value lies in its ability to generate plausible and testable hypotheses, not in achieving absolute certainty.  
* **LLM Instability and Hallucination:** Relying on LLMs for reasoning introduces the risk of factual incorrectness, inconsistency, and hallucination.20 The proposed multi-stage pipeline is designed to mitigate this risk. The LLM is not trusted as a final arbiter. Instead, its initial broad judgments are refined by a specialized LTR model, and its final inference is heavily constrained by structured evidence from the KG.  
* **Incorporating Domain Knowledge:** The process should not be a fully automated black box. Causal discovery algorithms perform significantly better when constrained by prior domain knowledge.40 The framework will be designed to support human-in-the-loop interaction, allowing a human expert to review the generated graph and impose constraints, such as adding known relationships, removing impossible ones, or fixing the orientation of certain edges. This synthesis of algorithmic discovery and human expertise is crucial for building robust and trustworthy causal models.40

To provide a clear rationale for the chosen methodology, the following table compares the proposed hybrid approach with other classes of causal discovery algorithms.

| Feature | Constraint-Based (e.g., PC) 39 | Score-Based (e.g., GES) 39 | LLM-Direct Prompting 43 | Proposed Hybrid (LLM+KG) 34 |
| :---- | :---- | :---- | :---- | :---- |
| **Core Paradigm** | Uses conditional independence tests to prune a fully connected graph. | Searches the space of graphs for one that maximizes a scoring function. | Directly prompts an LLM with variable names and context to infer a relationship. | Uses a KG to extract structural evidence, which is ranked and then used to ground an LLM's inference. |
| **Primary Input Data** | Tabular (numerical or categorical) data. | Tabular (numerical or categorical) data. | Natural language text (variable names, descriptions). | A knowledge graph (Semantic Memory) and natural language context. |
| **Key Assumptions** | Causal Markov Condition, Faithfulness, Acyclicity. | Acyclicity, specific distributional assumptions depending on the score. | Relies entirely on the LLM's implicit, pre-trained knowledge. No formal assumptions. | Assumes the KG contains meaningful (though noisy) causal information. Leverages LLM knowledge but grounds it in the KG. |
| **Handling Confounders** | Can detect the presence of latent confounders (e.g., FCI algorithm). | Generally assumes causal sufficiency (no latent confounders). | Prone to spurious correlations and "causal blindness"; struggles to distinguish correlation from causation.25 | Can identify potential confounding paths if they are represented in the KG structure. |
| **Scalability** | Computationally expensive for high-dimensional data due to many CI tests. | NP-hard in general, but heuristic searches are feasible for moderate numbers of variables. | Highly scalable, as it relies on a single LLM inference per pair. | Scalable, but with significant upfront cost for subgraph extraction and LTR model training. |
| **Suitability for Semantic Memory** | Poor. Requires conversion of graph structure to a tabular format, losing semantic richness. | Poor. Same limitations as constraint-based methods. | Moderate. Leverages semantic content but is prone to hallucination and lacks structural grounding. | **High.** Explicitly designed to leverage the rich semantic and structural information inherent in a knowledge graph. |

Table 3.1: Comparison of Causal Discovery Algorithms for Knowledge Graphs

## **Part IV: Generating and Integrating Counterfactual-Driven Plans**

This section operationalizes the causal model, detailing the process by which the Planner agent uses it to generate and integrate innovative research strategies. The goal is to move from a static causal model to a dynamic process of hypothesis generation and exploratory planning.

### **4.1 The Counterfactual Querying Process**

The ability to generate counterfactuals is not useful unless it is integrated intelligently into the agent's planning cycle. This requires a mechanism for triggering exploration and a method for formulating meaningful "what if" questions.

* **Triggering Exploration:** The Planner agent will be endowed with a policy that governs the trade-off between exploitation and exploration. Initially, this can be a heuristic-based policy. For instance, exploration via the Causal Reasoning Module could be triggered when:  
  * The system receives a novel research query that has a low semantic similarity score to any episode in the Episodic Memory.  
  * A standard plan retrieved from Episodic Memory repeatedly fails to yield high-quality results, suggesting the existing knowledge is insufficient.  
  * A periodic "curiosity" drive is activated, prompting the system to challenge a random, long-standing assumption in its Semantic Memory.  
* **Formulating the "What If" Question:** Once exploration is triggered, the Planner must formulate a specific counterfactual query. This is a form of automated hypothesis generation.19 The  
  Planner can analyze the topology of the causal DAG to identify promising targets. For example, it might select an edge with high betweenness centrality, as this represents a critical link in the domain's causal theory. If this edge is A→B, the query becomes: "What would the state of knowledge be if A did *not* cause B?".  
* **The Algorithm for Counterfactual Generation:** The CounterfactualGenerationEngine receives this query and executes the formal three-step algorithm 5:  
  1. **Abduction:** The engine first considers the factual world as represented by the Semantic Memory. It uses the SCM to infer the values of the unobserved exogenous noise variables (U) that are consistent with the observed facts. This step is crucial because it "grounds" the counterfactual in the specific context of the system's current knowledge, making the counterfactual a personalized "what if" for this specific world state, not a generic one.22  
  2. **Action (Mutilation):** The engine creates a copy of the SCM and performs a "graph surgery." It severs the link from A to B by removing or altering the structural equation for B that depends on A.  
  3. **Prediction:** Using the noise values inferred during abduction, the engine computes the new probability distributions for all variables in the mutilated SCM. This yields a complete, probabilistic description of the hypothetical world where A does not cause B.

### **4.2 From Counterfactual Outcomes to Exploratory Research Subgraphs**

The output of the counterfactual query is not a simple "yes" or "no" but a new, rich probability distribution over the variables in the domain. The Planner's role is to interpret this output and translate it into an actionable plan.

* **Interpreting the Result:** The Planner analyzes the counterfactual probability distribution to identify the most significant deviations from the factual world. For example, it might discover that in the world where A does not cause B, the probability of a third variable, C, causing B has increased dramatically.  
* **Generating a New Hypothesis:** This observation is then crystallized into a new, testable scientific hypothesis: "Variable C is a potential alternative cause for B, whose effect may be masked by the dominant influence of A in the observed data."  
* **Creating the Research Subgraph:** Finally, the Planner compiles this hypothesis into an executable research plan, structured as a subgraph to be integrated into the main workflow.1 This subgraph would instantiate a team of specialized agents with clear, targeted objectives. For example:  
  * A WebResearcher agent would be tasked to "Find and summarize academic papers that discuss a potential relationship between C and B."  
  * A DataAnalyzer agent (if equipped with appropriate tools) might be tasked to "Re-analyze existing datasets for a correlation between C and B after statistically controlling for the influence of A."

The following table provides a clear, step-by-step breakdown of this entire workflow, mapping the abstract causal theory to concrete agent actions.

| Step | Theoretical Name | Agent Responsible | Action | Input | Output |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 1 | **Query Formulation** | Planner | Identifies a key causal link (A→B) in the SCM to challenge. | Causal DAG, Research Context | A formal counterfactual query: "What if A did not cause B?" |
| 2 | **Abduction** | CounterfactualGenerationEngine | Infers the posterior distribution of exogenous noise variables $P(U | E)$ given evidence E from Semantic Memory. | SCM, Semantic Memory data |
| 3 | **Action** | CounterfactualGenerationEngine | Creates a "mutilated" SCM (M′) by removing the causal link A→B. | Original SCM, Counterfactual Query | A new SCM, M′, representing the hypothetical world. |
| 4 | **Prediction** | CounterfactualGenerationEngine | Computes the outcomes in the new model using the inferred noise values from Step 2\. | Mutilated SCM (M′), Inferred Noise U | A new probability distribution over all variables in the counterfactual world. |
| 5 | **Interpretation** | Planner | Compares the counterfactual distribution to the factual one and identifies significant changes. | Factual and Counterfactual Distributions | A natural language summary of the key difference, e.g., "C is now a likely cause of B." |
| 6 | **Subgraph Generation** | Planner | Translates the interpreted finding into a concrete, executable research plan with agent tasks. | Interpreted Finding | A new research subgraph with agent roles and objectives to test the new hypothesis. |

Table 4.1: The Counterfactual Generation Workflow

### **4.3 A New Planning Cycle: The Exploration-Exploitation Loop**

The introduction of this causal capability fundamentally changes the nature of planning in the system. The Supervisor and Planner agents must now manage a portfolio of research strategies, balancing the efficiency of reusing known plans with the innovative potential of exploring counterfactuals. To optimize this decision-making process over time, it is proposed to frame it as a **Causal Reinforcement Learning (CRL)** problem.46

Reinforcement learning and causal reasoning are natural complements. RL is concerned with selecting optimal interventions (actions) to maximize reward, while causality provides the tools to predict the effects of those interventions.50 In this context:

* **The State** would be the current state of the research, including the user query, the information accumulated in the main graph's State object, and the current causal model.  
* **The Action** would be the Planner's choice at the decision point: either to retrieve a specific plan from Episodic Memory (exploit) or to query the Causal Reasoning Module with a specific counterfactual question (explore).  
* **The Reward Signal** would be derived from the comprehensive evaluation metrics defined in Part V. This reward would be designed to value not just the quality of the final report, but also the novelty of the research path taken to produce it.

By applying RL techniques, the Planner can learn a sophisticated policy for *when* and *how* to ask counterfactual questions to maximize its long-term discovery of high-quality, novel information. This directly connects the causal reasoning module to the overarching goal of creating a self-improving research system, as outlined in the foundational system blueprint.1 The agent does not just follow a fixed heuristic; it learns to become a more creative and effective researcher over time.

## **Part V: A Framework for Evaluating Novelty and Discovery**

Evaluating the success of this research endeavor presents a significant challenge. Traditional metrics used for AI systems, such as task completion rate or accuracy on a question-answering benchmark, are insufficient. They fail to capture the primary goal, which is not just to produce correct answers, but to generate *innovative* and *creative* research paths.20 Therefore, a new evaluation framework is required, one that can quantify the concepts of novelty and utility in the context of automated research planning.

### **5.1 The Challenge: Moving Beyond Task Success**

The core problem is that standard evaluation metrics are misaligned with the goal of discovery. An agent that generates a highly novel but ultimately fruitless research plan would be penalized by a success-based metric, while an agent that safely regurgitates a known-good plan would be rewarded. To overcome this, the evaluation framework must be built on a more nuanced understanding of creativity.

Drawing from decades of research in cognitive science and creativity studies, a creative product is widely defined as one that is both **novel** and **useful** (or valuable, effective).51 An idea that is novel but not useful is merely original; an idea that is useful but not novel is merely an optimization. True creativity lies at the intersection of both. Our evaluation framework must therefore be designed to measure these two dimensions independently and in combination.

### **5.2 A Proposed Suite of Novelty and Utility Metrics**

To operationalize the concepts of novelty and utility, a suite of new metrics is proposed. These metrics will be calculated for each research plan generated by the system, allowing for a quantitative assessment of its creative potential and success.

* **Metric 1: Structural Divergence (Novelty Score)**  
  * **Concept:** This metric quantifies the originality or "strangeness" of a generated research plan by measuring how different its structure is from previously known plans.  
  * **Implementation:** A research plan is represented as a graph. To calculate the novelty of a new, causally-generated plan, it will be compared against the top-k most semantically similar plans stored in the system's Episodic Memory. The divergence will be measured using established graph similarity metrics, such as Graph Edit Distance or the Jaccard similarity of their node and edge sets. A higher distance score indicates a more novel plan, as it deviates more significantly from established patterns. This approach is inspired by work in creativity evaluation that measures novelty based on similarity to existing artifacts.51  
* **Metric 2: Hypothesis Quality (Plausibility Score)**  
  * **Concept:** This metric assesses the intrinsic quality and promise of the underlying hypothesis that an exploratory research plan is designed to test. A novel plan is only valuable if it is based on a plausible, testable idea.  
  * **Implementation:** An LLM-as-a-Judge pipeline, a technique already specified for final report evaluation in the base system 1, will be adapted for this task. A powerful, independent LLM (e.g., GPT-4o or Claude 4 Opus) will be given the generated hypothesis (e.g., "C is an alternative cause for B") and asked to score it against a formal rubric. This rubric will include criteria such as:  
    * **Plausibility:** Does the hypothesis make sense within the broader context of the scientific domain?  
    * **Testability:** Can a concrete experiment or analysis be designed to validate or refute the hypothesis?  
    * Potential Impact: If the hypothesis were proven true, would it represent a significant finding in the field?  
      This aligns with standard practices for evaluating LLM-generated content and hypotheses.20  
* **Metric 3: Research Utility (Success Score)**  
  * **Concept:** This metric measures the ultimate success of the research path. Did the novel plan, when executed, actually lead to a high-quality outcome?  
  * **Implementation:** This score will be directly derived from the comprehensive evaluation of the final research report produced by the system. It will leverage the hardened LLM-as-a-judge pipeline defined in the core system architecture, which assesses the report on dimensions like factual accuracy, completeness, coherence, and source quality.1  
* **Metric 4: Creative Utility (Composite Score)**  
  * **Concept:** This is a single, composite metric designed to reward plans that are both original *and* effective, capturing the dual nature of creativity.  
  * Implementation: The score will be calculated as a weighted function of the novelty and success scores, for example:  
    $Creative\_Utility \= w \\times \\text{Structural\_Divergence} \+ (1-w) \\times \\text{Research\_Utility}$  
    The weight, w, is a hyperparameter that can be tuned to reflect the desired balance between exploration and exploitation for a given application. This approach is inspired by similar composite metrics like utility\_k proposed in the NoveltyBench benchmark, which combines novelty and quality measures.56

The following table summarizes these proposed metrics.

| Metric Name | Dimension Measured | Calculation Method | Purpose |
| :---- | :---- | :---- | :---- |
| **Structural Divergence** | Novelty / Originality | Graph similarity distance (e.g., Graph Edit Distance) between the generated plan and the top-k most similar plans in Episodic Memory. | To quantify how structurally different a new research plan is from existing, known strategies. |
| **Hypothesis Quality** | Plausibility / Promise | LLM-as-a-Judge scoring of the underlying hypothesis based on a rubric of plausibility, testability, and potential impact. | To assess the intrinsic merit of the exploratory idea before committing significant resources to its execution. |
| **Research Utility** | Usefulness / Success | Score from the final report evaluation pipeline, measuring factual accuracy, completeness, and source quality. | To measure the concrete, end-to-end success of the research path initiated by the plan. |
| **Creative Utility** | Overall Creativity | A weighted combination of the Structural Divergence and Research Utility scores. | To provide a single, holistic score that rewards plans for being both novel and effective, serving as the primary reward signal for RL. |

Table 5.1: Evaluation Metrics for Research Plan Novelty

### **5.3 Benchmarking and Human-in-the-Loop Evaluation**

The evaluation will be conducted through a rigorous, multi-pronged approach:

* **Comparative Analysis:** The primary evaluation will involve a head-to-head comparison of the causally-augmented Planner against the baseline Planner that relies solely on Episodic Memory. Performance will be measured across the full suite of metrics. The results can be visualized on a 2D Novelty-Utility plot, which should demonstrate a clear shift in the system's behavior from a high-utility/low-novelty quadrant to a high-utility/high-novelty quadrant.  
* **Human Expert Evaluation:** As the ultimate gold standard for scientific creativity, the hypotheses generated by the system will be benchmarked against those generated by human domain experts. In a blind study, a panel of experts will be asked to rate the novelty and potential impact of hypotheses from both the AI system and human researchers. This type of consensual assessment technique is the most reliable method for evaluating creative outputs and is a common practice in the field of automated hypothesis generation.21 This provides the crucial external validation needed to assess whether the system's "creativity" is meaningful.

## **Part VI: Phased Implementation and Research Roadmap**

This final section translates the comprehensive research plan into an actionable, phased development strategy. This roadmap is designed to manage complexity, deliver value incrementally, and provide clear milestones for a research and development team. It also outlines future research directions that build upon the foundation established by this project.

### **6.1 Phase 1: Foundational Causal Model Construction**

* **Objective:** To develop the core CausalDiscoveryEngine and demonstrate the feasibility of constructing a preliminary SCM from the system's Semantic Memory. This phase focuses on building the foundational data-to-model pipeline.  
* **Tasks:**  
  1. Implement the knowledge graph traversal algorithms for extracting metapath-based subgraphs.  
  2. Develop the LLM-powered relevance estimation and the Learning-to-Rank (LTR) model for subgraph refinement.  
  3. Implement the "KG Structure as Prompt" mechanism for final pairwise causal inference.  
  4. Design and implement the logic for assembling the discovered pairwise relationships into a global causal DAG.  
  5. Implement a basic SCM with linear structural equations as a first-pass approximation of the causal mechanisms.  
* **Milestone:** Successful generation of a plausible and coherent causal graph for a well-defined and constrained research domain (e.g., a specific area of biomedicine or a subfield of computer science) using the content of the Semantic Memory as the sole input. The graph should be validated by a human domain expert.

### **6.2 Phase 2: Counterfactual Generation and Planner Integration**

* **Objective:** To implement the CounterfactualGenerationEngine and integrate the full causal reasoning workflow into the Planner agent's decision cycle. This phase focuses on making the causal model actionable.  
* **Tasks:**  
  1. Implement the three-step abduction-action-prediction algorithm for generating counterfactual outcomes from the SCM.  
  2. Modify the Planner agent's core logic and prompting to enable it to formulate counterfactual queries based on the causal graph.  
  3. Develop the translation logic for converting a probabilistic counterfactual outcome into a new, executable research subgraph with clear agent objectives.  
  4. Implement a baseline heuristic policy for the Planner to balance exploitation (querying Episodic Memory) and exploration (querying the Causal Reasoning Module).  
* **Milestone:** A complete, end-to-end demonstration run. The system, given a query, should successfully formulate a counterfactual question, generate a novel hypothesis, compile it into a new research plan, and execute that plan. The final plan must be demonstrably different from any plan retrievable from Episodic Memory.

### **6.3 Phase 3: Advanced Optimization and Evaluation**

* **Objective:** To refine the system's performance and implement the full evaluation and self-improvement loop. This phase focuses on making the system not just capable, but measurably effective and intelligent.  
* **Tasks:**  
  1. Implement the complete suite of Novelty and Utility metrics as defined in Part V.  
  2. Develop and deploy a comprehensive evaluation dashboard to track these metrics over time.  
  3. Implement the Causal Reinforcement Learning (CRL) framework to train the Planner's exploration policy, using the Creative Utility metric as the primary reward signal.  
  4. Conduct large-scale comparative experiments against the baseline system and human experts.  
* **Milestone:** Quantitative evidence of learning. The system should demonstrate a statistically significant improvement in its average Creative Utility score over multiple training epochs, proving that it is learning to become a more effective and creative researcher.

### **6.4 Future Directions: Towards Autonomous Scientific Discovery**

The successful implementation of this blueprint provides a powerful foundation for several long-term research trajectories aimed at achieving true autonomous scientific discovery.

* **Dynamic Causal World Models:** The proposed system builds its causal model from the static Semantic Memory. A significant next step would be to enable the model to learn and update dynamically from the agent's own interactions with its environment (e.g., from the outputs of tool calls and the results of its research). This would transform the SCM into a true "Causal World Model" that adapts in real-time, a key goal in the integration of LLMs and causal reasoning.26  
* **Automated Experimentation:** The current proposal generates plans to *find* existing evidence for a hypothesis. A more advanced system would generate plans to *create* new evidence. This could involve designing and executing computational experiments—such as running simulations, training small-scale machine learning models, or performing statistical analyses on public datasets—to directly test the hypotheses generated through counterfactual reasoning.  
* **Causal-Grounded Self-Correction:** The base system includes a robust self-correction loop driven by a dedicated Evaluator agent.1 This capability could be profoundly enhanced by the causal model. When a failure occurs, the system could use the SCM to perform root-cause analysis, moving beyond simply correcting the error to understanding  
  *why* it occurred. This would enable the system to modify its underlying processes and agent behaviors to prevent entire classes of failures in the future.

A powerful, self-reinforcing feedback loop emerges from this architecture. The system uses its Semantic Memory to construct a causal model. This model is then used to conduct novel, counterfactual-driven research. The verified findings from this research are then consolidated back into the Semantic Memory by the MemoryManager agent.1 This act of consolidation enriches and improves the very knowledge base from which the causal model is built. This creates a virtuous cycle, a "flywheel of causal discovery," where the more the system explores using its causal model, the more accurate and comprehensive its causal model becomes, which in turn enables even more effective and ambitious exploration in the future. This flywheel represents the core mechanism for achieving long-term, autonomous self-improvement in the complex and open-ended domain of scientific discovery.

#### **Works cited**

1. Multi-Agent Research System Improvement.docx  
2. Causal deep learning \- van der Schaar Lab, accessed on June 16, 2025, [https://www.vanderschaar-lab.com/causal-deep-learning-research-pillar/](https://www.vanderschaar-lab.com/causal-deep-learning-research-pillar/)  
3. An Introduction to Causal Inference: 9781507894293: Pearl, Judea: Books \- Amazon.com, accessed on June 16, 2025, [https://www.amazon.com/Introduction-Causal-Inference-Judea-Pearl/dp/1507894295](https://www.amazon.com/Introduction-Causal-Inference-Judea-Pearl/dp/1507894295)  
4. A Complete Guide to Causal Inference \- Towards Data Science, accessed on June 16, 2025, [https://towardsdatascience.com/a-complete-guide-to-causal-inference-8d5aaca68a47/](https://towardsdatascience.com/a-complete-guide-to-causal-inference-8d5aaca68a47/)  
5. Learning Structural Causal Models through Deep Generative Models: Methods, Guarantees, and Challenges \- IJCAI, accessed on June 16, 2025, [https://www.ijcai.org/proceedings/2024/0907.pdf](https://www.ijcai.org/proceedings/2024/0907.pdf)  
6. milvus.io, accessed on June 16, 2025, [https://milvus.io/ai-quick-reference/what-are-structural-causal-models-scms\#:\~:text=Structural%20Causal%20Models%20(SCMs)%20are,how%20variables%20influence%20one%20another.](https://milvus.io/ai-quick-reference/what-are-structural-causal-models-scms#:~:text=Structural%20Causal%20Models%20\(SCMs\)%20are,how%20variables%20influence%20one%20another.)  
7. Causal inference in statistics: An overview \- UCLA, accessed on June 16, 2025, [https://ftp.cs.ucla.edu/pub/stat\_ser/r350.pdf](https://ftp.cs.ucla.edu/pub/stat_ser/r350.pdf)  
8. What are Structural Causal Models (SCMs)? \- Milvus, accessed on June 16, 2025, [https://milvus.io/ai-quick-reference/what-are-structural-causal-models-scms](https://milvus.io/ai-quick-reference/what-are-structural-causal-models-scms)  
9. What is Structural Causal Models (SCM) \- Activeloop, accessed on June 16, 2025, [https://www.activeloop.ai/resources/glossary/structural-causal-models-scm/](https://www.activeloop.ai/resources/glossary/structural-causal-models-scm/)  
10. What is Pearl's Causal Inference Framework? \- Milvus, accessed on June 16, 2025, [https://milvus.io/ai-quick-reference/what-is-pearls-causal-inference-framework](https://milvus.io/ai-quick-reference/what-is-pearls-causal-inference-framework)  
11. A Survey of Methods, Challenges and Perspectives in Causality \- arXiv, accessed on June 16, 2025, [https://arxiv.org/pdf/2302.00293](https://arxiv.org/pdf/2302.00293)  
12. What is Causal AI? Understanding Causes and Effects \- DataCamp, accessed on June 16, 2025, [https://www.datacamp.com/blog/what-is-causal-ai](https://www.datacamp.com/blog/what-is-causal-ai)  
13. Why Causal AI? | causaLens, accessed on June 16, 2025, [https://causalai.causalens.com/why-causal-ai/](https://causalai.causalens.com/why-causal-ai/)  
14. Using Causal Graphs to answer causal questions | Towards Data Science, accessed on June 16, 2025, [https://towardsdatascience.com/using-causal-graphs-to-answer-causal-questions-5fd1dd82fa90/](https://towardsdatascience.com/using-causal-graphs-to-answer-causal-questions-5fd1dd82fa90/)  
15. Counterfactual Explanations: The What-Ifs of AI Decision Making \- KPMG International, accessed on June 16, 2025, [https://kpmg.com/ch/en/insights/artificial-intelligence/counterfactual-explanation.html](https://kpmg.com/ch/en/insights/artificial-intelligence/counterfactual-explanation.html)  
16. How does AI perform counterfactual reasoning? \- Zilliz Vector Database, accessed on June 16, 2025, [https://zilliz.com/ai-faq/how-does-ai-perform-counterfactual-reasoning](https://zilliz.com/ai-faq/how-does-ai-perform-counterfactual-reasoning)  
17. Counterfactual Explanations in Machine Learning \- Lumenova AI, accessed on June 16, 2025, [https://www.lumenova.ai/blog/counterfactual-explanations-machine-learning/](https://www.lumenova.ai/blog/counterfactual-explanations-machine-learning/)  
18. Humans Use Counterfactuals to Reason About Causality. Can AI? | Stanford HAI, accessed on June 16, 2025, [https://hai.stanford.edu/news/humans-use-counterfactuals-reason-about-causality-can-ai](https://hai.stanford.edu/news/humans-use-counterfactuals-reason-about-causality-can-ai)  
19. Reimagining Urban Science: Scaling Causal Inference with Large Language Models \- arXiv, accessed on June 16, 2025, [https://arxiv.org/html/2504.12345v1](https://arxiv.org/html/2504.12345v1)  
20. A Survey on Hypothesis Generation for Scientific Discovery in the Era of Large Language Models \- arXiv, accessed on June 16, 2025, [https://arxiv.org/html/2504.05496v1](https://arxiv.org/html/2504.05496v1)  
21. Automating Psychological Hypothesis Generation with AI: Large Language Models Meet Causal Graph \- arXiv, accessed on June 16, 2025, [https://arxiv.org/html/2402.14424v2](https://arxiv.org/html/2402.14424v2)  
22. Causal Inference 3: Counterfactuals, accessed on June 16, 2025, [https://www.inference.vc/causal-inference-3-counterfactuals/](https://www.inference.vc/causal-inference-3-counterfactuals/)  
23. Causal Agent based on Large Language Model \- arXiv, accessed on June 16, 2025, [https://arxiv.org/pdf/2408.06849](https://arxiv.org/pdf/2408.06849)  
24. \[2408.06849\] Causal Agent based on Large Language Model \- arXiv, accessed on June 16, 2025, [https://arxiv.org/abs/2408.06849](https://arxiv.org/abs/2408.06849)  
25. A Survey on Enhancing Causal Reasoning Ability of Large Language Models \- arXiv, accessed on June 16, 2025, [https://arxiv.org/html/2503.09326v1](https://arxiv.org/html/2503.09326v1)  
26. arxiv.org, accessed on June 16, 2025, [https://arxiv.org/html/2410.19923v1](https://arxiv.org/html/2410.19923v1)  
27. \[2410.19923\] Language Agents Meet Causality \-- Bridging LLMs and Causal World Models \- arXiv, accessed on June 16, 2025, [https://arxiv.org/abs/2410.19923](https://arxiv.org/abs/2410.19923)  
28. LANGUAGE AGENTS MEET CAUSALITY ... \- OpenReview, accessed on June 16, 2025, [https://openreview.net/pdf?id=y9A2TpaGsE](https://openreview.net/pdf?id=y9A2TpaGsE)  
29. Language Agents Meet Causality \-- Bridging LLMs and Causal World Models | OpenReview, accessed on June 16, 2025, [https://openreview.net/forum?id=y9A2TpaGsE](https://openreview.net/forum?id=y9A2TpaGsE)  
30. (PDF) Language Agents Meet Causality \-- Bridging LLMs and Causal World Models, accessed on June 16, 2025, [https://www.researchgate.net/publication/385318258\_Language\_Agents\_Meet\_Causality\_--\_Bridging\_LLMs\_and\_Causal\_World\_Models](https://www.researchgate.net/publication/385318258_Language_Agents_Meet_Causality_--_Bridging_LLMs_and_Causal_World_Models)  
31. Daily Papers \- Hugging Face, accessed on June 16, 2025, [https://huggingface.co/papers?q=Language%20Agents](https://huggingface.co/papers?q=Language+Agents)  
32. \[2506.08771\] Paths to Causality: Finding Informative Subgraphs Within Knowledge Graphs for Knowledge-Based Causal Discovery \- arXiv, accessed on June 16, 2025, [https://arxiv.org/abs/2506.08771](https://arxiv.org/abs/2506.08771)  
33. Identifying causal relationships with knowledge graphs and large language models, accessed on June 16, 2025, [https://blog.metaphacts.com/identifying-causal-relationships-with-knowledge-graphs-and-large-language-models](https://blog.metaphacts.com/identifying-causal-relationships-with-knowledge-graphs-and-large-language-models)  
34. Paths to Causality: Finding Informative Subgraphs Within Knowledge Graphs for Knowledge-Based Causal Discovery \- arXiv, accessed on June 16, 2025, [https://arxiv.org/html/2506.08771v1](https://arxiv.org/html/2506.08771v1)  
35. \[Literature Review\] Paths to Causality: Finding Informative ..., accessed on June 16, 2025, [https://www.themoonlight.io/en/review/paths-to-causality-finding-informative-subgraphs-within-knowledge-graphs-for-knowledge-based-causal-discovery](https://www.themoonlight.io/en/review/paths-to-causality-finding-informative-subgraphs-within-knowledge-graphs-for-knowledge-based-causal-discovery)  
36. Automating psychological hypothesis generation with AI: when large language models meet causal graph \- ResearchGate, accessed on June 16, 2025, [https://www.researchgate.net/publication/382110287\_Automating\_psychological\_hypothesis\_generation\_with\_AI\_when\_large\_language\_models\_meet\_causal\_graph](https://www.researchgate.net/publication/382110287_Automating_psychological_hypothesis_generation_with_AI_when_large_language_models_meet_causal_graph)  
37. Knowledge Graph Structure as Prompt: Improving Small Language Models Capabilities for Knowledge-based Causal Discovery \- ResearchGate, accessed on June 16, 2025, [https://www.researchgate.net/publication/382639119\_Knowledge\_Graph\_Structure\_as\_Prompt\_Improving\_Small\_Language\_Models\_Capabilities\_for\_Knowledge-based\_Causal\_Discovery](https://www.researchgate.net/publication/382639119_Knowledge_Graph_Structure_as_Prompt_Improving_Small_Language_Models_Capabilities_for_Knowledge-based_Causal_Discovery)  
38. Learning causal structure from data — DoWhy documentation \- PyWhy, accessed on June 16, 2025, [https://www.pywhy.org/dowhy/v0.11/user\_guide/modeling\_causal\_relations/learning\_causal\_structure.html](https://www.pywhy.org/dowhy/v0.11/user_guide/modeling_causal_relations/learning_causal_structure.html)  
39. Interactive Causal Discovery in Knowledge Graphs \- CEUR-WS.org, accessed on June 16, 2025, [https://ceur-ws.org/Vol-2465/semex\_paper4.pdf](https://ceur-ws.org/Vol-2465/semex_paper4.pdf)  
40. Human-Guided Causal Discovery | causaLens, accessed on June 16, 2025, [https://causalai.causalens.com/human-guided-causal-discovery/](https://causalai.causalens.com/human-guided-causal-discovery/)  
41. KCRL: A Prior Knowledge Based Causal Discovery Framework with Reinforcement Learning, accessed on June 16, 2025, [https://proceedings.mlr.press/v182/hasan22a/hasan22a.pdf](https://proceedings.mlr.press/v182/hasan22a/hasan22a.pdf)  
42. PC algorithm for causal discovery from observational data without latent confounders — dodiscover v0.0.0 \- PyWhy, accessed on June 16, 2025, [https://www.pywhy.org/dodiscover/dev/tutorials/markovian/example-pc-algo.html](https://www.pywhy.org/dodiscover/dev/tutorials/markovian/example-pc-algo.html)  
43. Large Language Models for Causal Discovery: Current Landscape and Future Directions, accessed on June 16, 2025, [https://arxiv.org/html/2402.11068](https://arxiv.org/html/2402.11068)  
44. Beyond Correlation: Towards Causal Large Language Model Agents in Biomedicine \- arXiv, accessed on June 16, 2025, [https://arxiv.org/html/2505.16982v1](https://arxiv.org/html/2505.16982v1)  
45. Computing Counterfactuals — DoWhy documentation \- PyWhy, accessed on June 16, 2025, [https://www.pywhy.org/dowhy/v0.11/user\_guide/causal\_tasks/what\_if/counterfactuals.html](https://www.pywhy.org/dowhy/v0.11/user_guide/causal_tasks/what_if/counterfactuals.html)  
46. A Survey on Causal Reinforcement Learning \- arXiv, accessed on June 16, 2025, [https://arxiv.org/pdf/2302.05209](https://arxiv.org/pdf/2302.05209)  
47. Causal Information Prioritization for Efficient Reinforcement Learning \- arXiv, accessed on June 16, 2025, [https://arxiv.org/html/2502.10097v1](https://arxiv.org/html/2502.10097v1)  
48. 9 Reinforcement Learning \- Applied Causal Inference, accessed on June 16, 2025, [https://appliedcausalinference.github.io/aci\_book/11-reinforcement-learning.html](https://appliedcausalinference.github.io/aci_book/11-reinforcement-learning.html)  
49. Causal Discovery and Reinforcement Learning: A Synergistic Integration, accessed on June 16, 2025, [https://proceedings.mlr.press/v186/mendez-molina22a/mendez-molina22a.pdf](https://proceedings.mlr.press/v186/mendez-molina22a/mendez-molina22a.pdf)  
50. When Should Reinforcement Learning Use Causal Reasoning? \- OpenReview, accessed on June 16, 2025, [https://openreview.net/forum?id=D1PPuk8ZBI](https://openreview.net/forum?id=D1PPuk8ZBI)  
51. Evaluating and Enhancing Large Language Models for Novelty Assessment in Scholarly Publications \- ACL Anthology, accessed on June 16, 2025, [https://aclanthology.org/2025.aisd-main.5.pdf](https://aclanthology.org/2025.aisd-main.5.pdf)  
52. (PDF) Using AI to Evaluate Creative Designs \- ResearchGate, accessed on June 16, 2025, [https://www.researchgate.net/publication/266053077\_Using\_AI\_to\_Evaluate\_Creative\_Designs](https://www.researchgate.net/publication/266053077_Using_AI_to_Evaluate_Creative_Designs)  
53. Managing the Creative Frontier of Generative AI: The Novelty-Usefulness Tradeoff, accessed on June 16, 2025, [https://cmr.berkeley.edu/2023/07/managing-the-creative-frontier-of-generative-ai-the-novelty-usefulness-tradeoff/](https://cmr.berkeley.edu/2023/07/managing-the-creative-frontier-of-generative-ai-the-novelty-usefulness-tradeoff/)  
54. Full article: Recognizing, evaluating, and selecting new ideas: the problematic journey of novelty, accessed on June 16, 2025, [https://www.tandfonline.com/doi/full/10.1080/14479338.2024.2359383](https://www.tandfonline.com/doi/full/10.1080/14479338.2024.2359383)  
55. A Survey on Hypothesis Generation for Scientific Discovery in the Era of Large Language Models \- ResearchGate, accessed on June 16, 2025, [https://www.researchgate.net/publication/390601965\_A\_Survey\_on\_Hypothesis\_Generation\_for\_Scientific\_Discovery\_in\_the\_Era\_of\_Large\_Language\_Models](https://www.researchgate.net/publication/390601965_A_Survey_on_Hypothesis_Generation_for_Scientific_Discovery_in_the_Era_of_Large_Language_Models)  
56. NoveltyBench: Evaluating Creativity and Diversity in Language Models \- arXiv, accessed on June 16, 2025, [https://arxiv.org/html/2504.05228v1](https://arxiv.org/html/2504.05228v1)
