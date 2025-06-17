

# **Architecting Agent Memory: A Comparative Analysis of RAG and Fine-Tuning for Procedural Skill Recall**

## **Section 1: Executive Summary & Strategic Recommendation**

### **1.1 Core Mandate**

This report addresses the technical directive P4-05, which mandates a comprehensive investigation to determine the most effective and efficient architectural strategy for implementing procedural memory in AI agents. As per blueprint objective P4-01, this "procedural memory" is defined as the agent's capacity to learn, store, recall, and reliably execute "skills"—generalized sequences of successful tool invocations. The central question is whether to encode these skills by injecting them into the model's prompt at runtime via Retrieval-Augmented Generation (RAG) or by embedding them into the model's weights through Supervised Fine-Tuning (SFT). This analysis provides a definitive, data-backed recommendation to guide this critical architectural decision.

### **1.2 Synopsis of Findings**

The investigation reveals a complex landscape of trade-offs between RAG and fine-tuning, where neither approach is unilaterally superior. A clear dichotomy emerges across key operational and performance axes. Fine-tuning excels in performance-critical areas, offering significantly lower inference latency (\~50% reduction in some cases 1) and reduced computational cost at runtime due to smaller token loads. It is unparalleled for teaching an agent a specific

*behavior*, *style*, or the syntactic structure of tool usage. However, its primary drawback is its static nature; updating the agent's skill set requires a resource-intensive, time-consuming, and technically complex retraining and redeployment cycle.2

Conversely, RAG offers superior flexibility and maintainability. Skills can be added, updated, or removed by simply modifying an external knowledge base, a process that can be fully automated.4 This approach grounds the agent's responses in authenticated, up-to-date information, drastically reducing the risk of factual hallucinations.2 This agility, however, comes at the cost of increased inference latency (potentially 30-50% higher 7) and higher runtime costs due to the overhead of the retrieval step and larger prompt contexts.1 Furthermore, a "scalability paradox" becomes apparent: as the library of skills grows, the complexity of accurately retrieving the correct skill from a semantically crowded space becomes a significant bottleneck, shifting the system's complexity from model training to the retrieval mechanism itself.

### **1.3 The Hybrid Imperative**

The most compelling conclusion from this analysis is that a hybrid architecture, which synergistically combines fine-tuning and RAG, represents the optimal path forward. This is not merely a compromise but a demonstrably superior solution that leverages the strengths of each approach to mitigate the weaknesses of the other. Quantitative evidence from a comprehensive AWS case study provides strong validation for this conclusion. In the study, a hybrid model combining a fine-tuned Amazon Nova model with a RAG system improved response quality on domain-specific questions by 83% compared to the base model. This significantly outperformed both the fine-tuning-only and RAG-only approaches, which each yielded a 30% improvement.1 The hybrid model allows a smaller, more cost-effective model to achieve performance nearly on par with a much larger one, presenting a clear path to both high performance and operational efficiency.

### **1.4 Strategic Recommendation**

Based on the exhaustive analysis detailed in this report, the unequivocal recommendation for technical leadership is to **pursue a hybrid RAG and Fine-Tuning architecture for implementing agent procedural memory**.

This strategy involves a clear division of labor:

* **Fine-Tuning** should be used to teach the agent the fundamental *behavior* and *syntax* of tool use. By training on a curated dataset of diverse tool-calling examples, the model internalizes the general patterns of how to structure API calls, handle parameters, and reason about tool sequences. It learns *how to think like a tool user*.  
* **RAG** should be used at runtime to provide the dynamic, contextual, and declarative *data* necessary to execute those learned behaviors effectively. It retrieves specific, up-to-date information—such as user data, product IDs, or relevant documentation snippets—that the fine-tuned model then uses to populate the arguments of its tool calls.

This synergistic approach creates an agent that is both procedurally competent and factually grounded, addressing the core requirements of the P4-01 objective.

### **1.5 High-Level Roadmap**

The proposed path to realizing this architecture involves a structured, three-phase proof-of-concept (PoC) designed to validate these findings within our specific operational context.

1. **Phase 1: Foundation (Dataset & Evaluation):** Construction of a high-quality, procedural skill dataset using automated generation techniques, alongside the development of a robust evaluation harness with metrics tailored for tool-use correctness.  
2. **Phase 2: Implementation (Parallel PoCs):** Development of two parallel tracks: a RAG-only system and a fine-tuned model.  
3. **Phase 3: Synthesis & Analysis (Comparative Evaluation):** Rigorous testing of the base model, RAG-only, fine-tuned-only, and the proposed hybrid model against the evaluation harness to produce a final, data-backed report confirming the recommended architecture.

## **Section 2: Conceptual Foundations: Modeling Procedural Memory in AI Agents**

### **2.1 Defining "Procedural Memory" in an Engineering Context**

To architect a system for agent memory, it is first essential to establish a precise and actionable definition of the concept itself. The term "procedural memory" is borrowed from cognitive science, and understanding its origins provides critical context for its engineering application.

#### **Cognitive Science Perspective**

In cognitive science and neuroscience, memory is broadly divided into two long-term systems: declarative and procedural memory.9

* **Declarative Memory** is the memory of facts and events. It is explicit, meaning it can be consciously recalled and verbalized. It is often described as "knowing that"—for example, knowing that Paris is the capital of France.10 This system relies neurologically on the medial temporal lobe and connected cortical regions.12  
* **Procedural Memory**, in contrast, is the memory for skills and habits. It is implicit, meaning it operates without conscious awareness.9 It is described as "knowing how"—for example, knowing how to ride a bicycle, play a musical instrument, or solve a Rubik's cube.9 Learning in this system is gradual, occurring through practice and repetition, and once acquired, allows skills to be executed rapidly and automatically.13 This system is supported by a different neural network, primarily involving the fronto-striatal circuits, including the basal ganglia and cerebellum.9

#### **Engineering Analogy (P4-01)**

For the purposes of this project, we adopt an engineering analogy of this cognitive concept. "Procedural memory" for an AI agent is defined as **its learned and internalized capability to reliably recall and execute a generalized sequence of tool calls to achieve a specific goal**. This is the agent's "knowing how" to use its available tools. A "skill" is the fundamental unit of this memory—a stored, successful, and generalizable tool sequence. For instance, a skill could be the multi-step process of checking a user's calendar availability, finding a free slot, and then creating a meeting invitation using three distinct tool calls. The agent must not only know the individual tools but also the correct procedure for combining them.

### **2.2 The "Knowing How" vs. "Knowing What" Dilemma for Agent Skills**

With a working definition established, a deeper and more consequential question arises: what is the most effective way to *teach* an agent this "knowing how"? The conventional assumption is that we must provide the agent with explicit, step-by-step procedural instructions. However, recent research into the cognitive capabilities of Large Language Models (LLMs) reveals a critical nuance that fundamentally shapes our architectural recommendation.

#### **The Declarative/Procedural Tension in LLMs**

A 2024 study by Li et al. directly investigated how providing declarative versus procedural knowledge affects LLM performance on complex tasks.10 The researchers designed an experiment where, for a given problem, an LLM was provided with either:

1. **Declarative Hints:** All the necessary facts, concepts, and contextual information required to solve the problem ("knowing that").  
2. **Procedural Hints:** A step-by-step guide on the process or sequence of actions needed to solve the problem ("knowing how").

The findings were striking: for the majority of tasks, providing the model with **declarative knowledge led to significantly greater performance improvements** than providing procedural knowledge. The study concluded that procedural hints were only superior for reasoning tasks involving very simple, linear logic. For anything more complex, the models were more effective when given the "what" and allowed to infer the "how."

#### **Implication for Skill Representation**

This finding has profound implications for how we should design an agent's skill library. It suggests that attempting to encode skills as abstract, procedural rule sets may be a suboptimal strategy. Instead, a more effective approach is to reframe our "skills" as a library of **high-quality, declarative examples of successful tool usage**.

Rather than teaching the agent an abstract procedure like:  
1\. Call 'get\_user\_id(name)'. 2\. Call 'get\_calendar(user\_id)'. 3\. Call 'create\_invite(calendar, details)'.  
We would store a concrete, declarative example:  
USER\_REQUEST: "Book a meeting with Jane Doe about the Q3 launch."  
SUCCESSFUL\_EXECUTION: {"tool\_calls":}  
In this paradigm, the agent learns "how" to perform a task by being shown "what" a successful execution looks like. This reframing creates a natural and powerful synergy between RAG and fine-tuning, moving the discussion away from a simple "RAG vs. FT" competition and toward an understanding of their complementary roles in a more sophisticated architecture.

* **RAG's Natural Role:** RAG is an architecture fundamentally designed to retrieve and inject *declarative context* at runtime.4 Its purpose is to provide facts, examples, and grounding information. It is perfectly suited to retrieving the most relevant  
  *declarative skill example* for a given user task.  
* **Fine-Tuning's Natural Role:** Fine-tuning is a mechanism designed to teach a model a new *behavior, style, or underlying pattern*.3 It excels at adapting a model to a specific output format or reasoning process. It is perfectly suited to learning the  
  *general pattern* of how to interpret a user request and a retrieved example, and then generate a correctly formatted tool-calling sequence.

By defining skills as declarative examples, we align the problem with the inherent strengths of our two primary architectural choices, paving the way for a hybrid solution that is more effective than either approach in isolation.

## **Section 3: Architectural Deep Dive: RAG vs. Fine-Tuning for Skill Encoding**

Building on the conceptual foundation, this section provides a detailed technical breakdown of how Retrieval-Augmented Generation (RAG) and Supervised Fine-Tuning (SFT) would be implemented as standalone solutions for encoding and recalling agent skills.

### **3.1 The RAG-based Skill Library: Dynamic Retrieval and In-Context Execution**

A RAG-based system treats the agent's skills as an external knowledge base that is accessed on-demand at inference time. The core principle is that the model's internal parameters remain static; knowledge is provided dynamically through the prompt context.3

#### **Core Mechanics**

The operational flow of a RAG pipeline for procedural skill recall involves several distinct steps 5:

1. **Skill Library Creation:** A corpus of "skills" is created and stored externally. Following the principle from Section 2.2, these are not abstract rules but concrete, documented examples of successful tool sequences. Each skill document would contain a natural language description of the task it accomplishes and the corresponding sequence of tool calls.  
2. **Indexing:** This corpus is processed by an embedding model, which converts each skill document into a high-dimensional vector representation that captures its semantic meaning. These vectors are then stored and indexed in a specialized vector database (e.g., Milvus, Pinecone, FAISS).5 This process creates a searchable knowledge library that the agent can query.  
3. **User Query and Retrieval:** When a user issues a command (e.g., "Find my most recent sales report and email it to my manager"), the system first uses the same embedding model to convert this query into a vector.18 The retriever component then performs a similarity search (e.g., cosine similarity or approximate nearest neighbor search) against the vector database to find the skill document whose embedding is most semantically similar to the query vector.6 In this case, it might retrieve a skill for "find\_report\_and\_send\_email".  
4. **Prompt Augmentation:** The content of the retrieved skill document is then automatically injected into the context window of the LLM, alongside the original user query. This technique is sometimes referred to as "prompt stuffing".20 The final prompt effectively says:  
   Here is the user's request: 'Find my most recent sales report and email it to my manager.' And here is an example of a similar, successful task: \[content of the retrieved skill document\]. Now, generate the appropriate tool calls.  
5. **Grounded Generation:** The LLM, now equipped with both the user's specific intent and a relevant example, generates the final sequence of tool calls. The generation is "grounded" in the retrieved context, making it more likely to be accurate and correctly formatted.6

#### **Knowledge Source**

In the RAG architecture, the "knowledge" of how to perform skills is entirely externalized. It resides within the vector database and is accessed at runtime.4 The base LLM itself is not modified; it acts as a reasoning engine that leverages the dynamically provided information.21 This separation of knowledge and reasoning is a defining characteristic of RAG.

#### **Advantages**

The primary advantage of this approach is its dynamism and flexibility. In environments where new agent skills are frequently developed or existing ones are updated, RAG provides a low-friction path for maintenance. An update only requires modifying the external skill documents and re-indexing them, a process that can be fully automated and does not involve the costly and complex process of retraining the LLM.2 This makes RAG exceptionally well-suited for agile development environments and rapidly evolving problem domains.

### **3.2 The Fine-Tuned Skill Set: Embedding Procedural Knowledge into Model Weights**

In contrast to RAG, a fine-tuning approach internalizes the agent's skills by directly modifying the LLM's parameters. The goal is to create a specialized model that has "learned" the desired procedural behaviors.16

#### **Core Mechanics**

The process of creating a fine-tuned agent is a supervised learning task that occurs before deployment 16:

1. **Dataset Preparation:** A high-quality, labeled dataset is meticulously prepared. This dataset consists of hundreds or thousands of prompt-response pairs.16 For this use case, each pair would be:  
   * **Prompt:** A natural language user instruction (e.g., "What's on my schedule for tomorrow?").  
   * Response (Completion): The ideal, perfectly formatted sequence of tool calls required to fulfill that instruction (e.g., \[{"tool\_name": "get\_tomorrow\_date"}, {"tool\_name": "lookup\_calendar\_events", "parameters": {"date":...}}\]).  
     The quality, diversity, and accuracy of this dataset are paramount to the success of the fine-tuning process.15  
2. **Model Selection:** A pre-trained base model is chosen as the starting point. The selection should be based on its suitability for the task, considering factors like its inherent reasoning capabilities, context window size, and compatibility with the training infrastructure.16  
3. **Supervised Fine-Tuning (SFT):** The base model is further trained on the prepared dataset. During this training process, the model makes predictions for each prompt, and the difference (or "loss") between its prediction and the correct labeled response is calculated. An optimization algorithm, such as gradient descent, then adjusts the model's internal weights (billions of parameters) to minimize this loss over many iterations (epochs).16 This process effectively "teaches" the model the specific patterns, syntax, and reasoning structures present in the skill dataset. This can be done via full fine-tuning or more efficient methods like Parameter-Efficient Fine-Tuning (PEFT), such as Low-Rank Adaptation (LoRA), which updates only a small subset of the model's parameters.4  
4. **Inference:** Once the fine-tuning process is complete, the resulting specialized model is deployed. When this model receives a user query at inference time, it generates the corresponding tool call sequence directly from its internalized knowledge. It does not need to retrieve any external information, as the procedural capability has been baked into its parameters.7

#### **Knowledge Source**

With fine-tuning, the procedural knowledge becomes static and is embedded directly within the model's architecture.19 The model's ability to perform skills is a result of its adjusted weights, not external context.

#### **Advantages**

The key advantage of fine-tuning is its ability to teach the model a new *behavior* or *style*, not just new facts.3 For the highly structured and syntactically rigid domain of tool calling, this is a significant benefit. The model doesn't just learn

*that* a certain tool exists; it learns the nuanced *how* of invoking it correctly in various contexts. This can lead to more reliable and consistent behavior, especially for complex, multi-step reasoning, and it does so with lower inference latency since the retrieval step is eliminated.

## **Section 4: A Multi-faceted Comparative Analysis**

This section provides a systematic and exhaustive comparison of the RAG and fine-tuning approaches, evaluated against the critical axes of performance, scalability, generalization, and resource implications. This analysis forms the evidence base for the final architectural recommendation.

### **4.1 Performance and Reliability: Latency, Cost, and Execution Fidelity**

Performance is not a monolithic concept; it must be deconstructed into latency, cost, and the reliability of the agent's actions.

#### **Latency**

Latency, the time from user query to agent response, is a critical factor in user experience, especially for real-time interactive applications.

* **Fine-Tuning:** This approach consistently demonstrates **lower inference latency**. Because the procedural knowledge is embedded within the model's weights, the agent can generate a tool-calling sequence in a single forward pass. There is no need for an external data retrieval step, which is often a significant bottleneck.7 An AWS case study quantitatively confirmed this, finding that fine-tuning Amazon Nova models reduced the base model's latency by approximately 50%.1 This makes fine-tuning the preferred choice for applications with stringent real-time performance constraints.7  
* **RAG:** This architecture inherently introduces **higher latency**. The end-to-end process requires at least two steps: first, retrieving the relevant skill from the vector database, and second, passing the augmented prompt to the LLM for generation.8 Industry analysis suggests this additional step can increase total response times by 30–50% compared to a non-RAG model.7 While optimizations like efficient indexing (e.g., FAISS) can mitigate this, the retrieval overhead remains a fundamental characteristic of the RAG architecture.21

#### **Inference Cost**

The cost of running the model for each user query is a major operational consideration.

* **Fine-Tuning:** Can be significantly **more cost-effective at inference time**. This is due to two primary factors. First, a smaller, specialized model fine-tuned for a specific task can often achieve better performance than a much larger, general-purpose model, leading to direct cost savings on model hosting.8 Second, because the model has internalized the task's context, it requires shorter prompts, reducing token consumption. The AWS study found that fine-tuned models reduced the average total token count (input and output) by over 60%.1  
* **RAG:** Typically incurs **higher inference costs**. The primary driver is the increase in prompt size; the retrieved context must be added to the user's query, which can substantially increase the number of input tokens sent to the LLM.8 The AWS case study, for example, saw the average total token count more than double with the RAG approach.1 Additionally, there are operational costs associated with running the retrieval system and vector database for every query.31

#### **Reliability (Execution Fidelity & Hallucinations)**

Reliability refers to the agent's ability to consistently execute tasks correctly and avoid generating false or nonsensical information (hallucinations).

* **RAG:** Offers superior protection against **factual hallucinations**. Because the LLM's response is grounded in specific, authenticated information retrieved from a trusted knowledge base, it is less likely to invent incorrect parameters or arguments for tool calls.2 This grounding provides a "fact-checking" mechanism at the point of generation, making it highly reliable for tasks that depend on accurate, real-time data.32  
* **Fine-Tuning:** Reduces hallucinations by deeply specializing the model in a specific domain, making it an expert on the training data.2 However, it remains vulnerable in two key ways. First, it can still generate erroneous or imaginative responses when faced with unfamiliar queries or edge cases not covered in its training data.2 Second, it is susceptible to a phenomenon known as  
  **catastrophic forgetting**, where the process of learning new, specialized information overwrites or degrades the model's general knowledge learned during pre-training.19 This could impair its broader reasoning capabilities.

### **4.2 Scalability and Maintenance: The Operational Lifecycle of an Agent's Skills**

Scalability and maintenance examine how each architecture behaves as the system evolves and the number of agent skills grows over time.

#### **Adding/Updating Skills**

The agility to modify the agent's skill set is a crucial aspect of long-term maintenance.

* **RAG:** Is far **more flexible and agile**. To add a new skill or update an existing one, an operator simply needs to add or modify a document in the external knowledge base and re-index it.4 This process is computationally cheap, can be fully automated, and allows for near-real-time updates to the agent's capabilities without any model downtime.5  
* **Fine-Tuning:** Is inherently **static and rigid**. Any change to the skill set, no matter how small, necessitates a new training dataset and a complete retraining and redeployment cycle.2 This is a significant undertaking that is computationally expensive (requiring GPU clusters), time-consuming, and demands considerable MLOps expertise to manage effectively.3

#### **The Scalability Paradox and the Importance of the Retriever**

While the ease of updating knowledge suggests RAG is more scalable, a deeper analysis reveals a significant challenge as the number of distinct skills increases.

1. **The Common Wisdom:** The prevailing view is that RAG is more scalable because adding knowledge is inexpensive (updating a database) compared to fine-tuning, where adding knowledge is expensive (retraining the model).17  
2. **The Nature of Procedural Skills:** This assumption holds for adding factual documents to a knowledge base. However, our use case involves a library of distinct, executable skills. As this library grows from tens to thousands of skills, the semantic space becomes increasingly crowded. The natural language distinction between a request for search\_emails(query, sender) and search\_documents(query, author) can be very subtle.  
3. **The Retriever Bottleneck:** A standard vector-based retriever, which relies on semantic similarity, may begin to struggle to disambiguate between these subtly different skills. Retrieving the wrong skill example is a critical failure mode, as it will lead the LLM to generate a completely incorrect tool call sequence, causing the task to fail.  
4. **Shifting Complexity:** Therefore, the true bottleneck to scaling a RAG-based skill system is not the capacity of the data store, but the **accuracy and sophistication of its retriever**. As the system scales, maintaining high retrieval precision requires moving beyond simple vector search to more advanced techniques like hybrid search (combining keyword and semantic search) 6, adding a re-ranker model to score and re-order retrieved results 6, or implementing agentic RAG, where an agent can iteratively refine its own search query.34  
5. **Conclusion:** The scalability of RAG for procedural skills is not a given. It comes with a hidden cost and complexity: the need to build and maintain an increasingly intelligent retrieval system. The operational burden shifts from the MLOps of training to the data engineering and algorithmic complexity of the retriever.

In contrast, a fine-tuned model internalizes the ability to distinguish between skills during training. While scaling the training dataset is costly, once deployed, its performance does not depend on a fallible runtime retrieval component.

### **4.3 Generalization and Adaptability: Applying Skills to Novel Scenarios**

Generalization is the model's ability to apply what it has learned to new, unseen situations.

* **RAG:** Demonstrates superior adaptability to **new information**. Because it can dynamically pull from external knowledge sources, it can answer questions or perform tasks related to data that did not exist when the base model was trained.4 It is designed for generalization across a broad spectrum of dynamically changing knowledge.35  
* **Fine-Tuning:** Excels at **task specialization and style generalization**. By training on a specific type of data, it learns the underlying structure, format, and nuances of that task.28 This allows it to generalize the  
  *pattern* of the task to new inputs. For our use case, a model fine-tuned on tool-calling examples may be better at generating a syntactically correct call for a completely new, unseen tool, because it has learned the abstract concept of "how to format an API call." However, it is also prone to overfitting, where it performs well on data similar to its training set but fails on inputs that deviate too much.33

A pure RAG approach is limited by the examples it can retrieve. If a user makes a request for which no similar skill example exists in the database, the RAG system will likely fail. A fine-tuned model, having learned the general behavior, has a better chance of making a reasonable attempt.

### **4.4 Security, Cost, and Resource Implications**

Practical implementation is governed by constraints related to security, budget, and available expertise.

* **Security & Privacy:** RAG is widely considered the **superior architecture for enterprise data security**. Proprietary or sensitive data (e.g., customer PII needed for a tool call) resides in a secured, access-controlled external database. It is only brought into the model's context for a specific query and is not embedded in the model's weights.3 In fine-tuning, this data becomes part of the training set and is baked into the model itself, creating a larger potential attack surface and raising data governance concerns.17  
* **Upfront Cost & Skills:** Fine-tuning has a **much higher upfront cost**. It requires significant investment in compute resources (powerful GPUs), time for training runs, and a team with specialized expertise in deep learning, NLP, and MLOps.2 Setting up a RAG system is generally cheaper and requires more common software engineering and data architecture skills.2  
* **Runtime Cost & Complexity:** The cost profile inverts at runtime. A fine-tuned model has a **simpler and cheaper runtime architecture**.3 RAG introduces  
  **higher runtime costs and complexity** due to the continuous operation of the retrieval system and the larger prompt sizes, as discussed previously.3

---

To provide a consolidated view of this multi-faceted analysis, the following table summarizes the key trade-offs.

**Table 4.1: Comprehensive Comparative Analysis Summary**

| Characteristic | RAG Approach | Fine-Tuning Approach | Key Evidence |
| :---- | :---- | :---- | :---- |
| **Inference Latency** | Higher, due to the added retrieval step. | Lower, as knowledge is embedded in model weights. | 1 |
| **Inference Cost** | Higher, due to larger prompts and retrieval computation. | Lower, due to shorter prompts and simpler architecture. | 1 |
| **Reliability (Factual)** | High. Grounded in external, authenticated data, reducing factual hallucinations. | Moderate. Reduces hallucinations within its domain but can still err on unfamiliar queries. | 2 |
| **Knowledge Updatability** | High. Skills updated by modifying the external database; near real-time. | Low. Requires a full, costly retraining and redeployment cycle for any update. | 4 |
| **Maintenance Overhead** | Focused on data pipelines and retriever performance. | Focused on MLOps, managing training jobs, and model versioning. | 3 |
| **Scalability (Skill Count)** | Challenged by retriever accuracy as skill library grows. | Challenged by the cost and complexity of retraining on ever-larger datasets. | 14 |
| **Generalization (Style)** | Low. Adopts the style of the base model, not the retrieved data. | High. Excels at learning a specific task structure, style, and format. | 3 |
| **Data Security** | High. Sensitive data remains in a secured external environment. | Lower. Proprietary data is embedded into the model's weights. | 3 |
| **Upfront Cost** | Lower. Cheaper to set up the initial infrastructure. | Higher. Requires significant compute, time, and data labeling for training. | 2 |
| **Required Skillset** | Software engineering, data architecture, information retrieval. | Deep learning, NLP, MLOps, hyperparameter tuning. | 2 |

---

## **Section 5: A Practical Framework for Implementation and Evaluation**

To move from theoretical analysis to a concrete, data-backed decision, a proof-of-concept (PoC) is necessary. This section outlines a practical framework for implementing and evaluating the RAG and fine-tuning approaches, addressing the core components of the proposed research agenda.

### **5.1 Constructing a Procedural Memory Dataset for Tool Use ("Skills")**

The foundation of any successful model customization effort, whether RAG or fine-tuning, is a high-quality dataset. Manually creating such a dataset for tool use is notoriously difficult, time-consuming, and expensive.37 Therefore, we propose leveraging automated generation techniques pioneered by leading research in tool-learning.

#### **The Challenge and Solution**

The primary challenge is creating a dataset that is not only accurate but also diverse and complex enough to teach an agent robust tool-use capabilities.27 The solution lies in using powerful, state-of-the-art LLMs to bootstrap the dataset creation process, a method validated by successful frameworks like

**ToolAlpaca** 39 and

**ToolLLM/ToolBench**.41 These frameworks demonstrate that an LLM like GPT-4 can be prompted to generate thousands of high-quality, multi-turn tool-use instances from a collection of real-world API documentation.

#### **Proposed Dataset Creation Process**

Our PoC will adopt a similar methodology, structured in four key stages:

1. **Tool Collection & Documentation:** The first step is to gather all internal tool APIs that the agent will be expected to use. For each tool, we must create clear, structured, and comprehensive documentation. This is a critical step, as the quality of this documentation will directly impact the quality of the generated data. Following the ToolAlpaca model, each tool's documentation should include a natural language description of its purpose, a detailed breakdown of its functions, and a formal specification of its parameters (name, type, description, required/optional status).43  
2. **Instruction Generation:** Using a state-of-the-art instruction-following LLM (e.g., GPT-4o, Claude 3.5 Sonnet), we will generate a diverse set of user instructions that necessitate the use of our tools. This generation process will be guided by prompts designed to elicit a wide range of scenarios, including single-tool calls, simple multi-tool sequences, and complex, conditional logic. As demonstrated by the ToolLLM project, ensuring diversity in the generated instructions is a pivotal factor for achieving good generalization in the final model.42  
3. **Solution Path Annotation:** For each generated instruction, we will use the same powerful LLM to annotate the ideal "solution path"—the correct sequence of tool calls that fulfills the request. To handle complex, multi-step reasoning, we will employ advanced prompting strategies. The Depth-First Search Decision Tree (DFSDT) algorithm, developed for ToolLLM, provides a powerful template. This method allows the annotator LLM to explore multiple potential paths, backtrack from errors, and ultimately select the most promising solution, yielding higher quality annotations than simpler methods.42  
4. **Data Formatting and Structuring:** The final output will be structured into a standardized machine-readable format, such as JSONL.26 Each entry in the dataset will be a complete record containing the user  
   instruction, the relevant tool\_documentation, and the ground-truth response (the annotated tool call sequence).24 This format is compatible with most fine-tuning and evaluation pipelines.

Throughout this process, the emphasis will be on **quality over quantity**.26 A smaller dataset of 500-1000 high-quality, diverse, and complex examples is more valuable than a large dataset of simple, repetitive tasks.

### **5.2 A Robust Evaluation Harness: Metrics and Benchmarks for Tool-Use**

Evaluating a tool-using agent requires a more sophisticated approach than standard NLP evaluation. Metrics like BLEU and ROUGE, which measure text similarity, are insufficient because they do not capture the functional correctness of the agent's actions.45 A tool call can be a single character off and be completely wrong. Our evaluation harness must assess the

*procedural correctness* of the agent's behavior.

#### **Essential Metrics for Procedural Correctness**

Our evaluation framework will be built on a suite of metrics designed to provide a holistic view of agent performance:

* **Task Success Rate:** The ultimate binary metric: did the agent's sequence of actions successfully accomplish the user's goal?.45  
* **Tool Selection Accuracy:** Did the model choose the correct tool or API for each step in the process? This is inspired by the "function relevance detection" component of the Berkeley Function-Calling Leaderboard (BFCL).48  
* **Argument Fidelity:** Were the parameters passed to the tool calls correct? This involves checking for factual accuracy (e.g., correct user ID) and proper formatting. The evaluation can use methods like regular expression matching and inclusive string matching, as demonstrated in an Amazon Bedrock fine-tuning example.49  
* **Procedural Correctness:** Was the sequence of tool calls logical, efficient, and free of redundant or incorrect steps? This aligns with the goals of the L0-Bench benchmark, which focuses on evaluating the correctness of step-by-step reasoning processes.50  
* **Latency and Cost:** End-to-end response time and total token consumption are critical operational metrics that must be tracked for every evaluation run.45

#### **LLM-as-a-Judge**

For more qualitative aspects of performance, such as the coherence of the reasoning trace or the overall helpfulness of the agent's attempt, we will employ an "LLM-as-a-Judge" methodology. This technique, used successfully in the AWS case study 1 and the ToolEval framework 51, involves using a powerful, impartial LLM (e.g., Claude 3.5 Sonnet) to score the agent's output on a predefined rubric. This provides a scalable way to assess aspects that are difficult to capture with automated metrics alone.

To ground our internal evaluation framework in the broader research landscape and to set clear performance targets, it is useful to review the state-of-the-art benchmarks and model capabilities.

---

**Table 5.1: Key Tool-Use Evaluation Benchmarks**

| Benchmark | Primary Focus | Key Metrics | Source |
| :---- | :---- | :---- | :---- |
| **ToolEval** | General tool-use capability, comparing solution paths. | Pass Rate, Win Rate | 51 |
| **SWE-Bench** | Agentic software engineering; resolving real GitHub issues. | Patch Success Rate | 52 |
| **BFCL** | Function calling across multiple languages and scenarios. | Function Relevance, Argument Accuracy | 48 |
| **ToolHop** | Evaluating complex, multi-hop tool use dependencies. | Accuracy | 53 |
| **UltraTool** | End-to-end tool utilization: planning, creation, and application. | Multi-step Planning Accuracy | 54 |
| **Tau-Bench** | Interactive, multi-turn conversations involving tool use. | Task Accomplishment | 52 |

---

This table demonstrates the maturity of the tool-use evaluation field and provides a solid foundation for designing our internal test suites. Furthermore, public scores on these benchmarks establish a baseline for what constitutes state-of-the-art performance. For example, recent benchmark scores show a clear hierarchy among leading models.

**State-of-the-Art Model Performance on Tool Use (BFCL Benchmark)** 48

* Claude 3.5 Sonnet: 90.20%  
* Meta Llama 3.1 405b: 88.50%  
* Claude 3 Opus: 88.40%  
* OpenAI GPT-4: 88.30%  
* GPT-4o: 83.59%

These scores provide a crucial performance target. Any model developed in our PoC should be evaluated in the context of these industry-leading results. If a proposed solution significantly underperforms these benchmarks, its viability must be questioned.

## **Section 6: Advanced Architectures: The Hybrid Paradigm**

The preceding analysis reveals that neither RAG nor fine-tuning alone represents a complete solution. RAG offers dynamic knowledge but suffers from latency and retrieval complexity. Fine-tuning offers low-latency behavioral specialization but is static and costly to maintain. This naturally leads to the consideration of hybrid architectures that combine the two, aiming to capture the benefits of both while mitigating their respective drawbacks.

### **6.1 The RAG-Enhanced Fine-Tuned Agent: An Optimal Architecture**

The most promising path forward is a synergistic architecture where a fine-tuned model is enhanced with a RAG pipeline at inference time. This approach establishes a clear and effective division of labor between the two techniques.33

#### **Architectural Blueprint**

The proposed hybrid architecture operates as follows:

1. **Foundation: The Fine-Tuned Base Model:** The process begins with fine-tuning a base LLM on the procedural skill dataset created in Section 5.1. The primary goal of this stage is **not** to teach the model specific facts or data. Instead, it is to teach the model the abstract **behavior, syntax, and style** of tool usage.3 The model learns the general structure of an API call, how to reason about chaining multiple calls together, and how to output responses in the precise, machine-readable format required by the tool execution engine. It internalizes the  
   *procedural competence* of how to act as a tool-using agent.  
2. **Runtime Enhancement: The RAG Pipeline:** At inference time, this specialized, fine-tuned model is connected to a RAG pipeline.57 When a user query arrives, the RAG component operates in parallel. Its role is to retrieve relevant  
   **declarative knowledge** from various enterprise data sources—customer databases, document repositories, real-time monitoring systems, etc. This is the up-to-date, contextual information needed to fulfill the user's specific request.  
3. **Synergistic Generation:** The final prompt sent to the fine-tuned LLM contains both the original user query and the rich, declarative context retrieved by RAG. The model then executes its task in a two-part harmony:  
   * It uses its **fine-tuned procedural ability** to correctly structure the thought process and the syntax of the required tool calls.  
   * It uses the **RAG-provided declarative context** to accurately populate the arguments of those tool calls with timely and specific data.

#### **The Symbiotic Relationship**

This hybrid model creates a symbiotic relationship where each component addresses the core weakness of the other. Fine-tuning provides the deep, domain-specific understanding of *how to perform a task*, while RAG provides the real-time, factually-grounded knowledge of *what data to use for that task*.55 This combination resolves the "knowing how" vs. "knowing what" dilemma. The model is fine-tuned to "know how" to call tools in general, and RAG provides the specific "knowing what" context for each individual invocation.

### **6.2 Case Study Analysis: Lessons from Real-World Implementations**

The superiority of the hybrid approach is not merely theoretical; it is validated by both quantitative and qualitative evidence from real-world enterprise implementations.

#### **Quantitative Evidence: The AWS Case Study**

A comprehensive case study by AWS provides the most direct and compelling evidence.1 The study evaluated four configurations for answering AWS-specific questions: a base model, a RAG-only model, a fine-tuned-only model, and a hybrid model.

* **Performance Uplift:** The results were unambiguous. Using an LLM-as-a-judge evaluation, the RAG-only and fine-tuned-only models each improved response quality by 30% over the base model. The **hybrid model, however, improved response quality by a staggering 83%**.  
* **Cost-Effectiveness:** The study also found that a smaller model (Amazon Nova Micro) configured with the hybrid architecture achieved performance nearly on par with a larger, more expensive model (Amazon Nova Lite). This suggests that the hybrid approach is not only the most performant but also potentially the most cost-effective solution for specialized tasks, as it allows for the use of smaller, more efficient base models.

#### **Qualitative Evidence: Industry Examples**

Several leading technology companies have implemented RAG-based systems that highlight key principles for our own architecture.

* **DoorDash:** The food delivery company uses a sophisticated RAG system to power its support chatbot for delivery contractors ("Dashers").59 The system retrieves relevant help articles and, crucially, past resolved support cases to inform its responses. This demonstrates the power of retrieving concrete examples. Furthermore, their use of an "LLM Guardrail" for real-time compliance checking and an "LLM Judge" for ongoing quality monitoring validates the evaluation strategy proposed in Section 5.2.  
* **LinkedIn:** To improve customer service, LinkedIn implemented a RAG system built upon a **knowledge graph** rather than a simple vector store of text documents.59 By retrieving structured sub-graphs of related issues, their system achieves higher retrieval accuracy and has reduced the median time to resolve support issues by 28.6%. This underscores the "retriever bottleneck" insight from Section 4.2—investing in a more sophisticated retrieval mechanism yields significant performance gains.  
* **Telescope and Ema:** These sales automation platforms use RAG to connect their AI agents directly to their customers' CRM and ERP systems.60 This allows them to provide highly personalized lead recommendations and generate custom sales reports based on real-time, structured enterprise data. This showcases RAG's primary strength: securely accessing dynamic, proprietary data to ground agent actions.

### **6.3 Future-Facing Architectures: Agentic and Knowledge-Graph RAG**

While the RAG-enhanced fine-tuned model represents the current state-of-the-art, it is important to consider the next wave of architectural evolution. Two emerging trends are particularly relevant: Agentic RAG and GraphRAG.

* **Agentic RAG:** This paradigm elevates the RAG process by introducing AI agents to manage the retrieval step itself.34 Instead of a static, single-shot retrieval, an "agentic" retriever can perform multi-step reasoning. It might first issue a broad query, analyze the results, and then issue a more refined query. It can pull from multiple, heterogeneous data sources (e.g., a document database and a SQL database) and synthesize the findings. It can even perform self-validation on the retrieved information before passing it to the generator LLM. This approach directly addresses the "retrieval complexity" bottleneck identified in our analysis, making the RAG system itself more robust and scalable.  
* **GraphRAG:** This technique changes the fundamental unit of retrieval. Instead of embedding and retrieving isolated chunks of text, knowledge is first modeled and stored as a **knowledge graph**, where entities are nodes and their relationships are edges. The retriever then fetches relevant subgraphs.20 This provides the generator LLM with far richer structural and relational context than a simple block of text.59 For our use case of procedural skills, this is extremely promising. The relationships between different tools, their shared parameters, and the typical sequences in which they are called can be explicitly modeled in the graph, leading to much more intelligent retrieval.

## **Section 7: Final Recommendation and Implementation Roadmap**

This final section synthesizes the entirety of the preceding analysis into a conclusive recommendation for technical leadership and outlines a concrete, phased roadmap for a proof-of-concept implementation.

### **7.1 Reaffirming the Hybrid Approach**

The evidence presented throughout this report leads to a clear and decisive conclusion: a **hybrid architecture that combines a fine-tuned LLM with a Retrieval-Augmented Generation (RAG) pipeline is the most performant, scalable, and robust solution** for implementing procedural memory in AI agents.

This approach systematically addresses the weaknesses of each standalone method.

* **It overcomes the static nature of fine-tuning:** The RAG component ensures the agent's actions are grounded in dynamic, up-to-date, and contextually relevant data, allowing the skill library to evolve without costly retraining cycles.33  
* **It mitigates the performance and reliability risks of RAG:** The fine-tuned base model provides a strong foundation of procedural competence, ensuring the agent understands the syntax and structure of tool use. This reduces the burden on the retriever to find a perfect example every time and improves the model's ability to generalize to novel tasks.55  
* **It is demonstrably superior:** Quantitative case studies show that the hybrid approach yields significantly higher quality and accuracy than either RAG or fine-tuning in isolation, while also offering a path to greater cost-efficiency by enabling smaller models to perform at the level of larger ones.1

### **7.2 Decision Framework**

While the hybrid model is the recommended strategic direction, the specific implementation can be tuned based on the primary business and technical drivers of a given application. The following matrix provides a clear decision-making framework for prioritizing one component over the other within the hybrid architecture.

---

**Table 7.1: Decision Matrix for Selecting RAG, Fine-Tuning, or a Hybrid Approach**

| Key Driver | Prioritize RAG When... | Prioritize Fine-Tuning When... | The Hybrid Approach is Optimal When... |
| :---- | :---- | :---- | :---- |
| **Knowledge Freshness** | The agent must act on real-time or frequently changing data (e.g., inventory levels, user account status, breaking news). | The procedural knowledge is stable and changes infrequently (e.g., standardized compliance workflows). | The agent needs to execute stable procedures using dynamic, real-time data (the most common enterprise scenario). |
| **Task Complexity** | The task is primarily knowledge-intensive, requiring the retrieval of specific facts or documents to complete. | The task requires learning a complex behavior, style, or a highly specific, non-negotiable output format. | The agent must learn a complex behavior that is then applied to a wide range of specific, fact-based instances. |
| **Cost Sensitivity** | Upfront development costs must be minimized, and the organization can tolerate higher per-query inference costs. | Long-term inference costs are the primary concern, and there is a budget for the initial, intensive training phase. | The goal is maximum performance and cost-efficiency, leveraging a smaller fine-tuned model to reduce token usage. |
| **Data Privacy** | The agent must handle sensitive or proprietary data (PII, financial records), which must remain in a secured external system. | The training data is non-sensitive, or the organization has robust governance for embedding data into model weights. | The agent must use sensitive data to execute a specialized, learned behavior, keeping the data external via RAG. |
| **Scalability of Skills** | The library of skills is expected to grow and change rapidly, requiring agile updates. | The library of skills is largely fixed and well-defined. | The core set of behaviors is stable, but the data and contexts they apply to are constantly expanding. |
| **Response Style Control** | Enforcing a specific tone or brand voice is a secondary concern to factual accuracy. | Enforcing a consistent brand voice, tone, or personality is a primary requirement for the agent. | The agent must adopt a specific persona (from fine-tuning) while providing factually accurate answers (from RAG). |

---

### **7.3 Proposed Implementation Roadmap (PoC)**

To validate this recommendation and de-risk the final implementation, a structured, eight-week proof-of-concept is proposed.

#### **Phase 1: Foundation (Weeks 1-3)**

* **Objective:** Create the core assets for training and evaluation.  
* **Key Activities:**  
  1. **Skill Selection:** Identify a core set of 10-20 representative skills for the agent.  
  2. **Documentation:** Generate structured, comprehensive documentation for each selected tool and its functions.  
  3. **Dataset Generation:** Following the methodology in Section 5.1, use a powerful LLM (e.g., GPT-4o) to generate an initial high-quality dataset of approximately 500 instruction-response examples for the selected skills.  
  4. **Evaluation Harness Construction:** Build the multi-faceted evaluation harness as described in Section 5.2, including automated metrics for success rate, tool selection, and argument fidelity, as well as an LLM-as-a-Judge prompt for qualitative scoring.

#### **Phase 2: PoC Implementation (Weeks 4-6)**

* **Objective:** Build and test the individual RAG and fine-tuning systems.  
* **Key Activities:** This phase will be conducted in two parallel tracks.  
  * **Track A (RAG-only):**  
    1. Set up a vector database (e.g., Milvus 19) and index the skill dataset.  
    2. Implement a retrieval pipeline using a framework like LangChain 18 or LlamaIndex.61  
    3. Connect the pipeline to a base LLM (e.g., Llama 3.1 8B) and test its performance.  
  * **Track B (Fine-Tuning-only):**  
    1. Select a fine-tuning framework optimized for efficiency, such as Unsloth or Axolotl.62  
    2. Fine-tune the same base LLM (Llama 3.1 8B) on the generated skill dataset using a PEFT method like LoRA.  
    3. Deploy and test the fine-tuned model.

#### **Phase 3: Comparative Evaluation & Reporting (Weeks 7-8)**

* **Objective:** Synthesize the findings and produce the final data-backed report (P4-03).  
* **Key Activities:**  
  1. **Benchmark Execution:** Run a comprehensive set of tests on four model configurations against the evaluation harness: (1) the base model, (2) the RAG-only model, (3) the fine-tuned-only model, and (4) the hybrid model (fine-tuned model from Track B enhanced with the RAG pipeline from Track A).  
  2. **Results Analysis:** Analyze the quantitative and qualitative results, focusing on the key metrics of procedural correctness, latency, and cost.  
  3. **Final Report:** Draft the final P4-03 deliverable, presenting the empirical data from the PoC to validate the strategic recommendation made in this report and provide a detailed plan for production deployment.

## **Appendix**

### **A. Glossary of Key Terms**

* **Retrieval-Augmented Generation (RAG):** An architectural framework that enhances an LLM's capabilities by enabling it to dynamically retrieve relevant information from an external knowledge base at inference time and use that information as context to generate a response.2  
* **Supervised Fine-Tuning (SFT):** The process of taking a pre-trained LLM and further training it on a smaller, labeled, domain-specific dataset to adapt its behavior and specialize its performance for a particular task.16  
* **Parameter-Efficient Fine-Tuning (PEFT):** A set of techniques (e.g., LoRA, QLoRA) that modify only a small subset of an LLM's parameters during fine-tuning, significantly reducing the computational cost and memory requirements compared to full fine-tuning.4  
* **Low-Rank Adaptation (LoRA):** A popular PEFT method that freezes the pre-trained model weights and injects trainable rank decomposition matrices into each layer of the Transformer architecture, drastically reducing the number of trainable parameters.8  
* **Vector Database:** A specialized database designed to store and query high-dimensional vector embeddings efficiently. It is a core component of RAG systems, enabling fast semantic similarity search.6  
* **Embeddings:** Numerical representations (vectors) of text, images, or other data in a high-dimensional space. These are generated by an embedding model and capture the semantic meaning of the data.14  
* **Hallucination:** A phenomenon where an LLM generates text that is plausible-sounding but factually incorrect, nonsensical, or not grounded in the provided source data.2  
* **Catastrophic Forgetting:** A problem in neural networks, particularly during fine-tuning, where learning new information causes the model to overwrite or lose previously learned knowledge.19

### **B. Sample "Skill" Dataset Entries**

**Sample for RAG Retrieval (Markdown Format):**

---

## **skill\_name: schedule\_team\_meeting skill\_id: PROC-001 description: Schedules a 30-minute meeting with a specified team for the next available weekday, finds a common free slot, and sends a calendar invitation.**

# **Skill: Schedule Team Meeting**

## **Goal**

To schedule a 30-minute meeting with all members of a specific team.

## **Tool Sequence**

1. get\_team\_members(team\_name: str) \-\> member\_list: list  
2. get\_calendars(user\_ids: list) \-\> calendar\_objects: list  
3. find\_free\_slot(calendars: list, duration\_minutes: int) \-\> slot: datetime  
4. create\_calendar\_invite(attendees: list, start\_time: datetime, title: str) \-\> status: str

## **Example Execution**

**User Request:** "Schedule a sync for the 'Frontend-Dev' team."

\*\*Execution Trace:\*\*json  
{  
"tool\_calls":  
}  
},  
{  
"tool\_name": "find\_free\_slot",  
"parameters": {  
"calendars": "\[...calendar\_objects...\]",  
"duration\_minutes": 30  
}  
},  
{  
"tool\_name": "create\_calendar\_invite",  
"parameters": {  
"attendees": \["user-101", "user-105", "user-210"\],  
"start\_time": "2025-10-28T14:30:00Z",  
"title": "Sync Meeting: Frontend-Dev Team"  
}  
}  
\]  
}  
**Sample for Supervised Fine-Tuning (JSONL Format):**

JSON

{"instruction": "I need to book a 30-minute sync for the 'Frontend-Dev' team as soon as possible.", "response": "}}, {\\"tool\_name\\": \\"find\_free\_slot\\", \\"parameters\\": {\\"calendars\\": \\"\[...calendar\_objects...\]\\", \\"duration\_minutes\\": 30}}, {\\"tool\_name\\": \\"create\_calendar\_invite\\", \\"parameters\\": {\\"attendees\\": \[\\"user-101\\", \\"user-105\\", \\"user-210\\"\], \\"start\_time\\": \\"2025-10-28T14:30:00Z\\", \\"title\\": \\"Sync Meeting: Frontend-Dev Team\\"}}\]", "tool\_documentation": "..."}  
{"instruction": "Can you find the latest performance report for Q3 and send it to my manager, Bob Smith?", "response": "", "tool\_documentation": "..."}

### **C. Detailed Evaluation Metrics and Formulas**

**Contextual Precision & Recall (for RAG Retriever Evaluation)** 47

These metrics evaluate the quality of the retrieved context against a ground-truth or "ideal" response.

* Contextual Precision: Measures how relevant the retrieved context is. It is the ratio of relevant items in the retrieved context to the total number of items in the retrieved context.  
  ContextualPrecision=∣Retrieved\_Items∣∣Relevant\_Items∩Retrieved\_Items∣​  
* Contextual Recall: Measures how well the retriever finds all relevant items. It is the ratio of relevant items in the retrieved context to the total number of relevant items in the ground truth.  
  ContextualRecall=∣Relevant\_Items\_in\_Ground\_Truth∣∣Relevant\_Items∩Retrieved\_Items∣​

**Bilingual Evaluation Understudy (BLEU) Score** 45

Primarily used for machine translation, it measures the precision of n-grams in the generated text compared to a reference text. A higher score indicates greater similarity.  
BLEU=BP⋅exp(∑n=1N​wn​logpn​)  
where BP is the brevity penalty, wn​ are weights (typically uniform), and pn​ is the modified n-gram precision.  
**Recall-Oriented Understudy for Gisting Evaluation (ROUGE) Score** 45

Used for summarization, it measures the recall of n-grams, word sequences, and word pairs between the generated text and a reference text.

* ROUGE-N: Measures overlap of n-grams.  
  ROUGE−N=∑S∈{RefSumm}​∑gramn​∈S​Count(gramn​)∑S∈{RefSumm}​∑gramn​∈S​Countmatch​(gramn​)​  
* **ROUGE-L:** Measures the longest common subsequence (LCS).

**LLM-as-a-Judge Prompt Structure (Adapted from AWS Case Study)** 1

JSON

{  
  "system\_prompt": "You are an impartial and expert judge for evaluating AI agent performance. Your task is to assess the quality of the tool-calling sequence generated by an AI agent in response to a user's instruction. Your evaluation must consider the correctness of the chosen tools, the accuracy of the parameters, the logical coherence of the sequence, and the overall effectiveness in achieving the user's goal.",  
  "prompt\_template": "\[Instruction\]\\n{user\_instruction}\\n\\n\\n{tool\_docs}\\n\\n\\n{agent\_tool\_calls}\\n\\n\\n\[Analysis\]\\nBegin your evaluation by providing a short, step-by-step analysis of the agent's performance. Be as objective as possible. Comment on tool selection, parameter accuracy, and sequence logic.\\n\\n\\nAfter providing your analysis, you must rate the agent's performance on a scale of 1 to 10 by strictly following this format: 'Rating: \[\[rating\]\]'.",  
  "output\_format": "\[\[rating\]\]"  
}

#### **Works cited**

1. Model customization, RAG, or both: A case study with Amazon Nova ..., accessed on June 17, 2025, [https://aws.amazon.com/blogs/machine-learning/model-customization-rag-or-both-a-case-study-with-amazon-nova/](https://aws.amazon.com/blogs/machine-learning/model-customization-rag-or-both-a-case-study-with-amazon-nova/)  
2. Retrieval-Augmented Generation vs Fine-Tuning: What's Right for ..., accessed on June 17, 2025, [https://www.k2view.com/blog/retrieval-augmented-generation-vs-fine-tuning/](https://www.k2view.com/blog/retrieval-augmented-generation-vs-fine-tuning/)  
3. RAG vs. Fine-Tuning: How to Choose \- Oracle, accessed on June 17, 2025, [https://www.oracle.com/artificial-intelligence/generative-ai/retrieval-augmented-generation-rag/rag-fine-tuning/](https://www.oracle.com/artificial-intelligence/generative-ai/retrieval-augmented-generation-rag/rag-fine-tuning/)  
4. RAG vs Fine-Tuning: Differences, Benefits, and Use Cases Explained \- Wevolver, accessed on June 17, 2025, [https://www.wevolver.com/article/rag-vs-fine-tuning-differences-benefits-and-use-cases-explained](https://www.wevolver.com/article/rag-vs-fine-tuning-differences-benefits-and-use-cases-explained)  
5. What is RAG? \- Retrieval-Augmented Generation AI Explained \- AWS, accessed on June 17, 2025, [https://aws.amazon.com/what-is/retrieval-augmented-generation/](https://aws.amazon.com/what-is/retrieval-augmented-generation/)  
6. What is Retrieval-Augmented Generation (RAG)? | Google Cloud, accessed on June 17, 2025, [https://cloud.google.com/use-cases/retrieval-augmented-generation](https://cloud.google.com/use-cases/retrieval-augmented-generation)  
7. RAG vs Fine Tuning: The Hidden Trade-offs No One Talks About \- B EYE, accessed on June 17, 2025, [https://b-eye.com/blog/rag-vs-fine-tuning/](https://b-eye.com/blog/rag-vs-fine-tuning/)  
8. RAG vs Fine Tuning: Quick Guide for Developers \- Vellum AI, accessed on June 17, 2025, [https://www.vellum.ai/blog/rag-vs-fine-tuning-complete-comparison](https://www.vellum.ai/blog/rag-vs-fine-tuning-complete-comparison)  
9. DECLARATIVE AND PROCEDURAL MEMORY IN L2 APTITUDE \- OSF, accessed on June 17, 2025, [https://osf.io/p7bnt/download](https://osf.io/p7bnt/download)  
10. Meta-Cognitive Analysis: Evaluating Declarative and Procedural Knowledge in Datasets and Large Language Models \- arXiv, accessed on June 17, 2025, [https://arxiv.org/html/2403.09750v1](https://arxiv.org/html/2403.09750v1)  
11. arXiv:2403.09750v1 \[cs.CL\] 14 Mar 2024, accessed on June 17, 2025, [https://arxiv.org/pdf/2403.09750](https://arxiv.org/pdf/2403.09750)  
12. The reliability and validity of procedural memory assessments used in second language acquisition research., accessed on June 17, 2025, [https://bilingualism.northwestern.edu/wp-content/uploads/2025/03/the-reliability-and-validity-of-procedural-memory-assessments-used-in-second-language-acquisition-research.pdf](https://bilingualism.northwestern.edu/wp-content/uploads/2025/03/the-reliability-and-validity-of-procedural-memory-assessments-used-in-second-language-acquisition-research.pdf)  
13. Working, declarative and procedural memory in specific language impairment \- PMC \- PubMed Central, accessed on June 17, 2025, [https://pmc.ncbi.nlm.nih.gov/articles/PMC3664921/](https://pmc.ncbi.nlm.nih.gov/articles/PMC3664921/)  
14. The distinction between RAG and fine-tuning \- Toloka, accessed on June 17, 2025, [https://toloka.ai/blog/the-distinction-between-rag-and-fine-tuning/](https://toloka.ai/blog/the-distinction-between-rag-and-fine-tuning/)  
15. Top 11 Tools and Practices for Fine-Tuning Large Language Models (LLMs) \- Eden AI, accessed on June 17, 2025, [https://www.edenai.co/post/top-10-tools-and-practices-for-fine-tuning-large-language-models-llms](https://www.edenai.co/post/top-10-tools-and-practices-for-fine-tuning-large-language-models-llms)  
16. Fine-tuning large language models (LLMs) in 2025 \- SuperAnnotate, accessed on June 17, 2025, [https://www.superannotate.com/blog/llm-fine-tuning](https://www.superannotate.com/blog/llm-fine-tuning)  
17. RAG Vs Fine Tuning: How To Choose The Right Method, accessed on June 17, 2025, [https://www.montecarlodata.com/blog-rag-vs-fine-tuning/](https://www.montecarlodata.com/blog-rag-vs-fine-tuning/)  
18. How to Make Your LLM More Accurate with RAG & Fine-Tuning | Towards Data Science, accessed on June 17, 2025, [https://towardsdatascience.com/how-to-make-your-llm-more-accurate-with-rag-fine-tuning/](https://towardsdatascience.com/how-to-make-your-llm-more-accurate-with-rag-fine-tuning/)  
19. Knowledge Injection in LLMs: Fine-Tuning vs. RAG \- Zilliz blog, accessed on June 17, 2025, [https://zilliz.com/blog/knowledge-injection-in-llms-fine-tuning-and-rag](https://zilliz.com/blog/knowledge-injection-in-llms-fine-tuning-and-rag)  
20. Retrieval-augmented generation \- Wikipedia, accessed on June 17, 2025, [https://en.wikipedia.org/wiki/Retrieval-augmented\_generation](https://en.wikipedia.org/wiki/Retrieval-augmented_generation)  
21. RAG vs Fine Tuning: Which Method to Choose \- Label Your Data, accessed on June 17, 2025, [https://labelyourdata.com/articles/rag-vs-fine-tuning](https://labelyourdata.com/articles/rag-vs-fine-tuning)  
22. RAG vs finetuning: Which Approach is the Best for LLMs? \- Data Science Dojo, accessed on June 17, 2025, [https://datasciencedojo.com/blog/rag-vs-finetuning-llm-debate/](https://datasciencedojo.com/blog/rag-vs-finetuning-llm-debate/)  
23. RAG vs. Fine-Tuning: Why Real-Time AI Outperforms Static Training \- DataMotion, accessed on June 17, 2025, [https://datamotion.com/rag-vs-fine-tuning/](https://datamotion.com/rag-vs-fine-tuning/)  
24. Fine-Tuning LLMs: A Guide With Examples \- DataCamp, accessed on June 17, 2025, [https://www.datacamp.com/tutorial/fine-tuning-large-language-models](https://www.datacamp.com/tutorial/fine-tuning-large-language-models)  
25. AI model fine-tuning concepts | Microsoft Learn, accessed on June 17, 2025, [https://learn.microsoft.com/en-us/windows/ai/fine-tuning](https://learn.microsoft.com/en-us/windows/ai/fine-tuning)  
26. What are Fine-tuning Datasets? Simply Explained \- FinetuneDB, accessed on June 17, 2025, [https://finetunedb.com/blog/finetuning-datasets-explained/](https://finetunedb.com/blog/finetuning-datasets-explained/)  
27. An introduction to preparing your own dataset for LLM training \- AWS \- Amazon.com, accessed on June 17, 2025, [https://aws.amazon.com/blogs/machine-learning/an-introduction-to-preparing-your-own-dataset-for-llm-training/](https://aws.amazon.com/blogs/machine-learning/an-introduction-to-preparing-your-own-dataset-for-llm-training/)  
28. RAG vs Fine-Tuning: A Comprehensive Tutorial with Practical Examples \- DataCamp, accessed on June 17, 2025, [https://www.datacamp.com/tutorial/rag-vs-fine-tuning](https://www.datacamp.com/tutorial/rag-vs-fine-tuning)  
29. RAG vs. fine-tuning: Choosing the right method for your LLM ..., accessed on June 17, 2025, [https://www.superannotate.com/blog/rag-vs-fine-tuning](https://www.superannotate.com/blog/rag-vs-fine-tuning)  
30. RAG vs Finetuning vs Prompt Engineering: Key AI Techniques \- Chitika, accessed on June 17, 2025, [https://www.chitika.com/rag-vs-finetuning-vs-prompt-engineering/](https://www.chitika.com/rag-vs-finetuning-vs-prompt-engineering/)  
31. Fine-Tuning vs RAG: Key Differences Explained (2025 Guide) \- Orq.ai, accessed on June 17, 2025, [https://orq.ai/blog/finetuning-vs-rag](https://orq.ai/blog/finetuning-vs-rag)  
32. RAG vs Fine Tuning LLMs: The Right Approach for Generative AI \- Aisera, accessed on June 17, 2025, [https://aisera.com/blog/llm-fine-tuning-vs-rag/](https://aisera.com/blog/llm-fine-tuning-vs-rag/)  
33. A complete guide to retrieval augmented generation vs fine-tuning \- Glean, accessed on June 17, 2025, [https://www.glean.com/blog/retrieval-augemented-generation-vs-fine-tuning](https://www.glean.com/blog/retrieval-augemented-generation-vs-fine-tuning)  
34. What is Agentic RAG? | IBM, accessed on June 17, 2025, [https://www.ibm.com/think/topics/agentic-rag](https://www.ibm.com/think/topics/agentic-rag)  
35. RAG vs. LLM Fine-Tuning: 4 Key Differences and How to Choose \- Acorn Labs, accessed on June 17, 2025, [https://www.acorn.io/resources/learning-center/rag-vs-fine-tuning/](https://www.acorn.io/resources/learning-center/rag-vs-fine-tuning/)  
36. RAG vs. Fine-tuning \- IBM, accessed on June 17, 2025, [https://www.ibm.com/think/topics/rag-vs-fine-tuning](https://www.ibm.com/think/topics/rag-vs-fine-tuning)  
37. How to Generate Instruction Datasets from Any Documents for LLM Fine-Tuning, accessed on June 17, 2025, [https://towardsdatascience.com/how-to-generate-instruction-datasets-from-any-documents-for-llm-fine-tuning-abb319a05d91/](https://towardsdatascience.com/how-to-generate-instruction-datasets-from-any-documents-for-llm-fine-tuning-abb319a05d91/)  
38. How to Create Custom Instruction Datasets for LLM Fine-tuning \- Firecrawl, accessed on June 17, 2025, [https://www.firecrawl.dev/blog/custom-instruction-datasets-llm-fine-tuning](https://www.firecrawl.dev/blog/custom-instruction-datasets-llm-fine-tuning)  
39. AI-Powered Paper Summarization about the arXiv paper 2306.05301v1, accessed on June 17, 2025, [https://www.summarizepaper.com/en/arxiv-id/2306.05301v1/](https://www.summarizepaper.com/en/arxiv-id/2306.05301v1/)  
40. the official code for "ToolAlpaca: Generalized Tool Learning for Language Models with 3000 Simulated Cases" \- GitHub, accessed on June 17, 2025, [https://github.com/tangqiaoyu/ToolAlpaca](https://github.com/tangqiaoyu/ToolAlpaca)  
41. ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs, accessed on June 17, 2025, [https://openreview.net/forum?id=dHng2O0Jjr](https://openreview.net/forum?id=dHng2O0Jjr)  
42. ToolLLM: Facilitating Large Language Models to Master 16000+ ..., accessed on June 17, 2025, [https://arxiv.org/abs/2307.16789](https://arxiv.org/abs/2307.16789)  
43. ToolAlpaca: Generalized Tool Learning for Language Models with 3000 Simulated Cases \- OpenReview, accessed on June 17, 2025, [https://openreview.net/pdf/4c9fa3fccb72373f1c86e4e1839e6ab6ad04e9db.pdf](https://openreview.net/pdf/4c9fa3fccb72373f1c86e4e1839e6ab6ad04e9db.pdf)  
44. ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs \- YouTube, accessed on June 17, 2025, [https://www.youtube.com/watch?v=QnsVevC2ICA](https://www.youtube.com/watch?v=QnsVevC2ICA)  
45. LLM Evaluation: Key Metrics, Best Practices and Frameworks \- Aisera, accessed on June 17, 2025, [https://aisera.com/blog/llm-evaluation/](https://aisera.com/blog/llm-evaluation/)  
46. How To Evaluate LLMs: Metrics That Drive Success \- Forbes, accessed on June 17, 2025, [https://www.forbes.com/councils/forbestechcouncil/2025/02/05/how-to-evaluate-llms-metrics-that-drive-success/](https://www.forbes.com/councils/forbestechcouncil/2025/02/05/how-to-evaluate-llms-metrics-that-drive-success/)  
47. LLM Evaluation Metrics: The Ultimate LLM Evaluation Guide \- Confident AI, accessed on June 17, 2025, [https://www.confident-ai.com/blog/llm-evaluation-metrics-everything-you-need-for-llm-evaluation](https://www.confident-ai.com/blog/llm-evaluation-metrics-everything-you-need-for-llm-evaluation)  
48. LLM Benchmarks: Overview, Limits and Model Comparison \- Vellum AI, accessed on June 17, 2025, [https://www.vellum.ai/blog/llm-benchmarks-overview-limits-and-model-comparison](https://www.vellum.ai/blog/llm-benchmarks-overview-limits-and-model-comparison)  
49. Customize Amazon Nova models to improve tool usage | AWS Machine Learning Blog, accessed on June 17, 2025, [https://aws.amazon.com/blogs/machine-learning/customize-amazon-nova-models-to-improve-tool-usage/](https://aws.amazon.com/blogs/machine-learning/customize-amazon-nova-models-to-improve-tool-usage/)  
50. L0-Reasoning Bench: Evaluating Procedural Correctness in Language Models via Simple Program Execution \- arXiv, accessed on June 17, 2025, [https://arxiv.org/html/2503.22832v2](https://arxiv.org/html/2503.22832v2)  
51. TOOLLLM: FACILITATING LARGE LANGUAGE MODELS TO MASTER 16000+ REAL-WORLD APIS \- OpenReview, accessed on June 17, 2025, [https://openreview.net/pdf?id=dHng2O0Jjr](https://openreview.net/pdf?id=dHng2O0Jjr)  
52. 40 Large Language Model Benchmarks and The Future of Model Evaluation \- Arize AI, accessed on June 17, 2025, [https://arize.com/blog/llm-benchmarks-mmlu-codexglue-gsm8k](https://arize.com/blog/llm-benchmarks-mmlu-codexglue-gsm8k)  
53. arXiv:2501.02506v2 \[cs.CL\] 7 Jan 2025, accessed on June 17, 2025, [https://arxiv.org/abs/2501.02506](https://arxiv.org/abs/2501.02506)  
54. \[2401.17167\] Planning, Creation, Usage: Benchmarking LLMs for Comprehensive Tool Utilization in Real-World Complex Scenarios \- arXiv, accessed on June 17, 2025, [https://arxiv.org/abs/2401.17167](https://arxiv.org/abs/2401.17167)  
55. Fine-Tuning or RAG \- Which AI Model Strategy Is Right for You?, accessed on June 17, 2025, [https://forage.ai/blog/fine-tuning-vs-knowledge-bases-rags-the-ultimate-guide-to-ai-model-optimization/](https://forage.ai/blog/fine-tuning-vs-knowledge-bases-rags-the-ultimate-guide-to-ai-model-optimization/)  
56. RAG vs Fine-Tuning: Choosing the Right Approach for Building LLM-Powered Chatbots, accessed on June 17, 2025, [https://dev.to/techahead/rag-vs-fine-tuning-choosing-the-right-approach-for-building-llm-powered-chatbots-3m3m](https://dev.to/techahead/rag-vs-fine-tuning-choosing-the-right-approach-for-building-llm-powered-chatbots-3m3m)  
57. Hybrid RAG: Definition, Examples and Approches \- Lettria, accessed on June 17, 2025, [https://www.lettria.com/blogpost/hybrid-rag-definition-examples-and-approches](https://www.lettria.com/blogpost/hybrid-rag-definition-examples-and-approches)  
58. RAG Architecture Explained: A Comprehensive Guide \[2025\] | Generative AI Collaboration Platform, accessed on June 17, 2025, [https://orq.ai/blog/rag-architecture](https://orq.ai/blog/rag-architecture)  
59. 10 RAG examples and use cases from real companies \- Evidently AI, accessed on June 17, 2025, [https://www.evidentlyai.com/blog/rag-examples](https://www.evidentlyai.com/blog/rag-examples)  
60. 9 powerful examples of retrieval-augmented generation (RAG) \- Merge.dev, accessed on June 17, 2025, [https://www.merge.dev/blog/rag-examples](https://www.merge.dev/blog/rag-examples)  
61. Top 9 RAG Tools to Boost Your LLM Workflows, accessed on June 17, 2025, [https://lakefs.io/blog/rag-tools/](https://lakefs.io/blog/rag-tools/)  
62. Finetune a model to think and use tools : r/LocalLLaMA \- Reddit, accessed on June 17, 2025, [https://www.reddit.com/r/LocalLLaMA/comments/1ladl6d/finetune\_a\_model\_to\_think\_and\_use\_tools/](https://www.reddit.com/r/LocalLLaMA/comments/1ladl6d/finetune_a_model_to_think_and_use_tools/)  
63. LLM Fine-Tuning Tools: Best Picks for ML Tasks in 2025 | Label Your Data, accessed on June 17, 2025, [https://labelyourdata.com/articles/llm-fine-tuning/top-llm-tools-for-fine-tuning](https://labelyourdata.com/articles/llm-fine-tuning/top-llm-tools-for-fine-tuning)