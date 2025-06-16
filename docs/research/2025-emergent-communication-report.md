
# **A Research Report on Emergent Communication Protocols for Multi-Agent Collaboration**

> **Deprecated:** Development of fully emergent communication protocols has been discontinued.
> The project now exclusively follows the LLM-Grounded Guided Evolution paradigm.
> See [ADR-003](../architecture/llm_grounded_guided_evolution.md) for details.

## **Executive Summary**

This report presents a comprehensive research analysis into the feasibility and design of emergent communication (EC) protocols for multi-agent systems, as mandated by the research spike P3-20. The strategic objective is to transcend hard-coded interaction patterns by enabling artificial intelligence (AI) agents to learn their own efficient, task-specific languages, thereby unlocking significant performance improvements in collaborative tasks. The investigation focuses on two primary deliverables: a detailed proof-of-concept (PoC) design for a reinforcement learning environment to train these protocols, and a rigorous comparative analysis of the trade-offs between fully emergent and guided evolution approaches.

The analysis reveals a fundamental dichotomy in the field. **Fully emergent protocols**, where agents develop a language from scratch, offer the theoretical potential for discovering a maximally efficient and compressed communication system perfectly optimized for a specific task. However, this approach is fraught with severe practical challenges, including profound training instability, a high propensity for communication collapse, and the resulting protocols are typically opaque, uninterpretable, and unable to generalize to new tasks or partners.

Conversely, **guided evolution** provides a pragmatic engineering solution. By introducing inductive biases, information-theoretic constraints, or grounding the protocol in prior knowledge, this paradigm steers the learning process towards more stable, robust, and useful outcomes. The most promising of these methods involves grounding the emergent language in natural language, for instance by leveraging Large Language Models (LLMs). This approach not only accelerates learning and enhances stability but also yields protocols that are inherently interpretable and capable of zero-shot generalization to ad-hoc teamwork scenarios, including collaboration with human users.

Based on this analysis, the report concludes with a strong recommendation to pursue the **guided evolution paradigm** for the initial PoC development. Specifically, a design that grounds the emergent protocol in natural language via an LLM-based auxiliary reward function offers the optimal balance of benefits. It directly addresses the project's performance goals while ensuring the resulting system is stable to train, interpretable for analysis, generalizable for future applications, and fundamentally safer from a governance and security perspective. This path provides a robust and extensible foundation for future research and development in advanced multi-agent collaboration.

## **Strategic Context and Problem Formulation**

The strategic rationale for this investigation, as outlined in P3-20, is to leverage reinforcement learning (RL) to foster the emergence of an effective, implicit collaboration strategy among AI agents, thereby moving beyond the limitations of predefined, hard-coded interaction patterns. The core objective is to explore the frontier of multi-agent systems where agents learn their own efficient, compressed, and task-specific language, a capability that promises significant gains in performance on complex, collaborative tasks.

This report addresses the central research question derived from this objective: How can a system be designed and evaluated where agents develop their own communication protocols, and what is the optimal balance between unconstrained, fully emergent learning and a more guided evolutionary approach? To answer this, the report provides a foundational understanding of the underlying theory, presents a detailed PoC design for an RL environment tailored to a group chat framework, and conducts a deep analysis of the critical trade-offs between these two principal paradigms.

## **Section 1: Theoretical Foundations of Emergent Communication in Multi-Agent Systems**

The study of emergent communication is situated within the broader field of Multi-Agent Reinforcement Learning (MARL). Understanding the foundational concepts of MARL is essential for designing a system capable of learning complex communicative behaviors.

### **The MARL Paradigm for Communication**

The problem of multiple intelligent agents learning to communicate and collaborate can be formally modeled as a **Partially Observable Stochastic Game (POSG)**, also referred to as a Partially Observable Markov Game. This framework is a multi-agent extension of the single-agent Partially Observable Markov Decision Process (POMDP). A POSG is defined by a set of agents, a set of global states, a joint action space, a state transition function, and a set of reward functions, one for each agent.2 The critical element is "partial observability," which means that each agent perceives the environment through its own private observation, which is only a partial and potentially noisy view of the true global state.1

In the context of a collaborative group chat, the environment is the shared chat interface and the associated task. The global state might include the user's ultimate goal, the complete set of documents or tools available to the team, and the full history of interactions. However, each individual agent's observation is partial; for example, an agent may only have access to its own assigned document or tool, making it impossible for it to solve the task alone.1 This information asymmetry creates the fundamental need for communication.

### **The Necessity of Communication**

In MARL, communication is not merely a beneficial feature; in partially observable environments, it is a necessity for effective coordination and task success.5 When agents cannot communicate, they must treat the actions of other learning agents as part of the environment's dynamics. Because all agents are learning and changing their policies simultaneously, this creates a

**non-stationary environment** from the perspective of any single agent.6 This "moving-target" problem is a primary cause of instability in MARL, often preventing algorithms from converging to an optimal policy.

Effective communication transforms this problem. By exchanging information, agents can compensate for their partial knowledge, build a more complete and shared understanding of the global state, and coordinate their actions towards a common goal.1 Instead of guessing the intentions of others, they can explicitly signal them, turning an unpredictable environment into a more structured and cooperative one.

### **The Centralized Training, Decentralized Execution (CTDE) Paradigm**

The challenges posed by non-stationarity and partial observability have led to the dominance of a specific training paradigm in the field of communication-enabled MARL (Comm-MADRL): **Centralized Training, Decentralized Execution (CTDE)**.5 The prevalence of this paradigm is not a matter of convenience but a direct and necessary response to the fundamental theoretical roadblocks of multi-agent learning.

The non-stationarity problem arises because if each agent learns independently, its learning target (e.g., the optimal action-value function) is constantly shifting as other agents' policies evolve.6 This makes it exceedingly difficult to find a stable learning signal. A fully decentralized training approach (Decentralized Training, Decentralized Execution \- DTDE) often fails to converge for this very reason.1

CTDE provides a structural solution to this dilemma. During the **centralized training** phase, the learning algorithm is granted access to global information that is unavailable to any single agent during execution. This includes the joint observations, actions, and messages of all agents.7 A centralized "critic" can then compute a stable, globally-informed value estimate (e.g., a joint Q-value) that is conditioned on this complete information. This stable value is used to train the individual, decentralized policies (the "actors") of each agent.5

This approach effectively solves the non-stationarity problem from the perspective of the learning update, as the critic's evaluation provides a consistent frame of reference. This is precisely what enables advanced techniques like **Differentiable Inter-Agent Learning (DIAL)**, where gradients can be backpropagated directly through the communication channels from one agent to another.10 Such a mechanism is only possible because, during training, the system is treated as a single, end-to-end differentiable network, a viewpoint that requires centralization.11

Once training is complete, the system switches to **decentralized execution**. The centralized critic is discarded, and each agent operates using only its own local policy and its partial observation of the environment.10 This satisfies the constraints of real-world deployment where agents are autonomous and do not have access to a global controller. Thus, CTDE is not merely a popular training scheme but a foundational architecture that makes the stable learning of complex coordinated behaviors, such as emergent communication, practically feasible.

## **Section 2: The Spectrum of Emergence: A Comparative Analysis of Protocol Paradigms**

The ambition to create agents that learn their own language can be approached from two distinct philosophical and technical standpoints: allowing a protocol to emerge entirely from scratch or guiding its evolution with predefined constraints and biases. This section analyzes these two paradigms and their associated trade-offs.

### **Paradigm 1: Fully Emergent Protocols (Learning from Scratch) – DEPRECATED**

In the fully emergent paradigm, agents begin as a *tabula rasa* with no predefined communication protocol. The language emerges *de novo*, driven solely by the agents' interactions with each other and the environment as they work to maximize a shared task reward.1 The protocol is a purely emergent property of this process.

The primary mechanism for this type of learning is standard multi-agent reinforcement learning. For instance, in **Reinforced Inter-Agent Learning (RIAL)**, communication is treated simply as another action in the agent's policy space. The agent learns which message to send at which time through trial and error, guided by the same environmental reward signal as its physical actions, using algorithms like Q-learning or policy gradients.10

While appealing in its purity, this approach faces significant challenges that have largely limited its practical application:

* **Instability and Communication Collapse:** Learning a shared language is a notoriously difficult joint exploration problem. Agents can easily converge on "shadowed equilibria," where a policy of ignoring the communication channel is a safer, more stable local minimum than attempting the complex coordination required to develop a useful protocol. This often leads to agents learning to disregard communication entirely.4  
* **Opacity and Lack of Interpretability:** Because the protocol is optimized purely for task success, the emergent symbols or message vectors are arbitrary and have no inherent meaning to a human observer. The resulting "alien" languages are extremely difficult to analyze, debug, or trust, posing a major barrier to deployment in human-centric systems.2  
* **Poor Generalization and Brittleness:** The emergent protocol becomes highly overfitted to the specific task, environment, and even the specific training partners. This leads to a lack of robustness. When paired with a new agent (even one trained separately on the same task) in an ad-hoc teamwork scenario, the protocol often breaks down, a problem known as failure in zero-shot coordination (ZSC).16

### **Paradigm 2: Guided Evolution (Learning with Constraints and Priors)**

The guided evolution paradigm addresses the failures of the fully emergent approach by steering the learning process. Instead of a blank slate, agents learn within a framework of explicit biases, constraints, or prior knowledge designed to encourage the emergence of protocols with desirable properties like stability, efficiency, and interpretability.4

This guidance can be implemented through several mechanisms:

* **Inductive Biases:** These methods add auxiliary loss terms to the agent's learning objective that provide a more direct and dense reward signal for communication itself. Seminal examples include **positive signaling**, which encourages an agent's messages to be informative about its internal state or observation, and **positive listening**, which encourages a receiving agent's actions to be causally influenced by the messages it receives.2 These biases help prevent communication collapse by making communication intrinsically rewarding.  
* **Information-Theoretic Constraints:** This approach applies principles from information theory to shape the protocol. The **Information Bottleneck (IB)** principle is a powerful example, framing communication as a trade-off between informativeness (how useful the message is for the task) and complexity (the "cost" or bitrate of the message).20 By penalizing complexity, the IB principle encourages agents to learn compressed, abstract, and efficient symbolic representations rather than simply transmitting raw data.21  
* **Contrastive Learning:** This technique can be used to induce a more structured and coherent communication system. The core idea is to treat messages from different agents in the same context as different "views" of the same underlying state. The learning objective then becomes to maximize the mutual information between these views, for example, by training the agents to produce similar message representations for similar environmental states.22 This encourages the emergence of a more symmetric and shared "understanding."  
* **Grounding in Natural Language:** This is a powerful and increasingly popular form of guidance that aligns the emergent protocol with human language. This can be achieved in several ways: using a Large Language Model (LLM) to generate synthetic natural language descriptions of agent states as a grounding signal 16, using natural language itself as a source of meaning to bootstrap communication 14, or even pre-training models on an emergent language corpus to improve their performance on downstream natural language tasks, demonstrating a structural link between the two.24

The historical trajectory of the field reveals a significant shift in objectives. Early research in deep emergent communication focused on the existential question: "Can agents learn to communicate from scratch to solve a task?".10 After establishing that this was possible, albeit with major practical issues, the focus shifted. The subsequent wave of research addressed the failures of the first by asking a more pragmatic question: "What inductive biases or constraints are necessary for more structured, robust, and useful languages to emerge?".4 This led to the development of the guided evolution techniques described above. The most recent and powerful incarnation of this trend is the integration with LLMs, which reframes the goal once more: "Can we ground emergent communication in natural language to make it directly interpretable, generalizable, and human-compatible by default?".14 This evolution marks a transition from pure, biologically-inspired simulation towards a pragmatic engineering discipline focused on building controllable, auditable, and useful communicative AI. The central trade-off is no longer simply performance versus no performance, but rather task-specific "alien" optimality versus general-purpose, human-aligned utility.20

### **Comparative Analysis and Trade-offs**

The choice between a fully emergent or guided evolution approach involves a series of critical trade-offs across multiple dimensions. The following table provides a comparative analysis based on the evidence from the research literature.

| Dimension | Fully Emergent Protocols | Guided Evolution Protocols |
| :---- | :---- | :---- |
| **Training Stability & Efficiency** | **Low.** Prone to communication collapse and getting stuck in "shadowed equilibria" where non-communication is a safer local minimum. Requires vast exploration and is highly sample-inefficient.4 | **High.** The guidance (auxiliary losses, priors) provides a dense, stable learning signal for communication, preventing collapse and accelerating convergence.4 |
| **Protocol Interpretability** | **Very Low.** The emergent "language" is typically a set of arbitrary, opaque symbols or vectors optimized for the task, not for human understanding. It is often described as "alien".2 | **High.** By design, protocols are guided towards human-understandable structures. Grounding in natural language makes them directly interpretable.16 Even biases like compositionality improve interpretability.26 |
| **Task-Specific Optimality** | **Potentially Very High.** Unconstrained learning can, in theory, discover a maximally compressed and efficient protocol perfectly tailored to the specific task, potentially outperforming any human-designed or guided system for that narrow task.1 | **Moderate to High.** The protocol is optimized for both task success and the guiding constraint. This may prevent it from reaching the absolute peak of task-specific efficiency if the guide imposes suboptimal structures.20 |
| **Generalization & Adaptability** | **Low.** The protocol is highly specialized to the training environment and partners. It often fails in zero-shot coordination (ZSC) with new, unseen teammates or when the task changes slightly.16 | **High.** Grounding in robust, general concepts (like natural language) allows for much better generalization. Agents can coordinate with new partners, including humans, in ad-hoc teamwork scenarios.14 |
| **Implementation Complexity** | **Low (Architecturally).** The core RL algorithm is standard. **High (Practically).** Extremely difficult to tune hyperparameters to achieve stable communication without it collapsing. | **High (Architecturally).** Requires more complex model architectures and loss functions (e.g., integrating an LLM, an IB loss). **Lower (Practically).** Easier to achieve convergence due to the more stable learning problem. |
| **Key Use Case** | Scientific inquiry into the fundamental principles of language evolution from first principles. Environments where a completely novel, maximally efficient encoding is the primary goal, and interpretability is secondary.29 | Practical applications requiring robust, reliable, and interpretable agent-agent or human-agent collaboration. Systems that need to generalize to new tasks or partners.14 |

## **Section 3: Proof-of-Concept Design for an Emergent Communication Environment**

This section details a proof-of-concept (PoC) design for an RL environment to train and evaluate emergent communication protocols within a group chat framework. The design adopts the **guided evolution** paradigm, specifically by grounding the emergent language in natural language, to ensure stability, interpretability, and robustness.

### **Architectural Overview**

The proposed architecture is based on the **Centralized Training, Decentralized Execution (CTDE)** paradigm, implemented using a **Multi-Agent Actor-Critic** model. To ensure scalability, all agents will utilize **parameter sharing**, meaning they share the weights of their policy and value networks. This is a standard, robust choice that balances learning efficiency with performance.5 Each agent consists of a policy network (the "actor") that determines its actions and messages, and the system is trained with the help of a centralized value network (the "critic") that evaluates the quality of joint actions.

### **The RL Environment (Formalized as a POSG)**

The environment is modeled as a Partially Observable Stochastic Game (POSG) centered around a collaborative task within a group chat.

* **Task Example: Collaborative Information Retrieval.** A team of AI agents must collaboratively answer a complex user query. The query is designed such that its answer requires synthesizing information from multiple, distinct sources (e.g., different documents, databases, or API tools). Each agent is assigned one of these private sources.  
* **State Space (S):** The global state, which is accessible only to the centralized critic during training, includes: the full text of the user's query, the content of all private documents/tools available to the team, the current state of the shared answer draft being composed, and the complete, unabridged chat history.  
* **Observation Space (Oi​):** Each agent i has a partial observation of the state. This includes: the user's query, the content of its own private document or the interface of its assigned tool, the public chat history, and any messages specifically addressed to it. Crucially, agent i cannot see the private information held by other agents, which establishes the partial observability and the need to communicate.1  
* **Action Space (Ai​):** The action space for each agent is a hybrid of environmental and communicative actions, reflecting the dual nature of the task.32  
  * **Environmental Actions (Ae​):** A discrete set of task-specific actions. For the information retrieval task, this could include actions like: \[read\_document, extract\_key\_info(query\_text), write\_to\_draft(text\_snippet), request\_human\_clarification, finalize\_answer\].  
  * **Communication Actions (Ac​):** This is the channel for emergent communication. The design proposes a **discrete vocabulary of learned symbols** (e.g., a set of 128 unique tokens). Using discrete symbols rather than continuous vectors has been shown to improve robustness and is more amenable to interpretation and human-agent interaction.33 The agent's full action at each timestep is a tuple  
    (ae​,m), where ae​∈Ae​ is the environmental action and m∈Ac​ is the message token to broadcast to the other agents.

### **The Reward Function (R): A Guided Evolution Approach**

The reward function is designed to drive both task completion and the emergence of an interpretable communication protocol.

* **Primary Task Reward (Rtask​):** A sparse, global, team-based reward is used to encourage cooperation. A reward of Rtask​=+1 is given to all agents if the team submits a correct and complete final answer within a specified time limit. A reward of 0 is given otherwise. This shared reward forces agents to learn to coordinate to achieve the collective goal.2  
* **Auxiliary Guidance Loss (Lguide​):** This is the core of the guided evolution design, aimed at grounding the emergent protocol in natural language.  
  * **Mechanism:** At each timestep t, after agent i receives its observation oti​, a pre-trained Large Language Model (LLM) is used to generate a concise, natural language description, dti​, of the agent's current state or intention. For example, if the agent's document contains financial data relevant to the query, the LLM might generate the description, "My document contains the Q4 financial report."  
  * The agent's policy network outputs a probability distribution over the emergent message vocabulary Ac​, from which it samples a token mti​.  
  * An auxiliary loss term, Lguide​, is introduced. This loss minimizes the distance between the learned embedding of the emergent token mti​ and the embedding of the natural language description dti​. This can be implemented as the cosine distance or mean squared error in a shared embedding space.  
  * This mechanism directly incentivizes the agent to learn a protocol where its abstract symbols correspond to human-understandable concepts, dramatically improving interpretability, stability, and the potential for generalization to human-agent teams.14  
* **Total Loss:** The final loss function for training the agent's policy is a weighted combination of the standard policy gradient loss (derived from Rtask​) and the guidance loss. The total objective for the policy πθ​ is to maximize J(θ)=E−λLguide​, where λ is a hyperparameter balancing task optimization and language grounding.

### **Agent Model Architecture**

The neural network for each agent will be structured as follows:

* An RNN, such as a GRU or LSTM, will serve as the core of the agent's policy. This network processes the sequence of observations and incoming messages, maintaining a hidden state ht​ that acts as the agent's memory of the conversation history.3  
* The output of the RNN, ht​, is fed into two separate output heads:  
  * **Action Head:** A linear layer followed by a softmax function to produce a probability distribution over the discrete environmental actions Ae​.  
  * **Communication Head:** A separate linear layer with a softmax function to produce a probability distribution over the discrete message vocabulary Ac​.  
* The centralized critic network will take the global state S and the joint action-message tuple from all agents to produce a single Q-value estimate, which is then used to provide a low-variance gradient for training the decentralized actor policies.

## **Section 4: Implementation Strategy and Risk Mitigation**

A successful implementation of the PoC requires a phased approach to de-risk the project and a proactive strategy for managing the inherent challenges of MARL and the risks associated with emergent behaviors.

### **Phased Implementation Roadmap**

A staged roadmap is proposed to incrementally build complexity and validate components:

1. **Phase 1: Simple Referential Games.** The initial phase will focus on isolating and validating the core communication learning mechanism. This will be done using a standard Lewis signaling game environment.13 In this simple setup, a "speaker" agent observes a target concept (e.g., a specific color or shape) and must send a message from the emergent vocabulary to a "listener" agent, which must then identify the target from a set of distractors. Success in this phase validates that the basic RL and guidance mechanisms can produce a meaningful communication protocol.  
2. **Phase 2: Single-Turn Collaborative Task.** The next phase will move to a simplified, single-turn version of the proposed group chat task. For example, a two-agent task where each agent holds one half of a password, and they must communicate to reconstruct the full password. This tests the integration of communication and environmental actions in a constrained setting.  
3. **Phase 3: Multi-Turn Dialogue and Full Task.** The final phase will scale the system to the full PoC design: a dynamic, multi-turn collaborative information retrieval task involving multiple agents and a more complex action space. This phase will build on the validated components from the previous stages and test the system's ability to handle sequential dialogue and long-term credit assignment.12

### **Addressing Key MARL Challenges**

The PoC design and implementation plan must proactively address known MARL challenges:

* **Non-Stationarity:** This is fundamentally addressed by the choice of the CTDE architecture, which provides a stable training signal via the centralized critic, as detailed in Section 1\.  
* **Multi-Agent Credit Assignment (MACA):** The use of a global, team-based reward makes it difficult to determine the contribution of each individual agent to the team's success. To address this, the PoC will incorporate a value decomposition network, such as VDN or QMIX. These methods extend the CTDE framework by learning to decompose the centralized, global Q-value into a sum of agent-specific utility functions, providing a more targeted reward signal for each agent's policy update.7  
* **Scalability:** To ensure the system scales to a larger number of agents, two mechanisms will be employed. First, **parameter sharing** across all agent policies keeps the number of learnable parameters constant regardless of team size. Second, an **attention mechanism** will be used for message integration. Instead of simply concatenating incoming messages, which scales poorly, an attention module allows each agent to learn to weigh the importance of messages from different teammates based on the current context, leading to a more scalable and effective communication system.3

### **Managing Emergent Risks**

The very "emergence" that this project seeks to harness is a double-edged sword. An unconstrained emergent system can produce behaviors that are not only unpredictable but also potentially insecure or misaligned with broader organizational goals. The implementation must therefore treat safety and governance as first-class design requirements.

The development of a private, compressed communication protocol between autonomous agents introduces novel risk vectors. Agents could potentially discover ways to create **covert sidechannels**, encoding and exfiltrating sensitive information in seemingly innocuous messages that bypass standard monitoring tools.38 Furthermore, the opaque nature of a fully emergent language makes

**auditability and compliance** nearly impossible. It would be difficult to demonstrate compliance with data handling regulations like GDPR if data provenance cannot be traced through a learned protocol that has no human-readable semantics.38

This context reframes the choice of the guided evolution paradigm. It is not merely a technique for improving performance but also a critical **safety and governance mechanism**. By grounding the emergent language in human-interpretable concepts, we constrain its properties within auditable and controllable bounds. The following mitigation strategies are essential:

* **Monitoring and Interpretability:** The system must include tools to continuously monitor the emergent protocol. Leveraging the LLM-based guidance mechanism, a reverse-translation module can be built to map emergent symbols back into natural language for human oversight. Key metrics, such as compositionality and the alignment between symbols and their intended concepts, should be tracked over time to detect semantic drift.15  
* **Governance and Authorization:** The system architecture must incorporate strict, dynamic authorization controls. An agent's permission to communicate or perform certain actions should not be static but should be gated based on the specific task context and its authorized role, a concept known as intent-based authorization.38  
* **Sandboxing:** All agents must operate within a strictly controlled computational environment. Their ability to interact with external systems, access files, or make network calls must be heavily restricted and logged to prevent any potential for sandbox evasion or unintended external actions.38

## **Section 5: Evaluation Framework and Future Research Trajectories**

Evaluating the success of an emergent communication system requires moving beyond simple task-based metrics. A holistic evaluation suite is necessary to measure not only performance but also the quality, efficiency, and robustness of the learned protocol.

### **Measuring Success Beyond Task Completion**

Simply measuring the final task success rate is an insufficient and potentially misleading metric. A high reward could be achieved through a clever, non-communicative policy, and it provides no insight into whether the communication itself is efficient, meaningful, or robust.2 Therefore, a multi-faceted evaluation framework is proposed:

* **Holistic Evaluation Suite:**  
  * **Task Performance:** The primary success metric, including task completion accuracy and time-to-completion.  
  * **Communication Efficiency:** Quantitative measures of the protocol's compactness. This includes metrics like the average message length and the entropy of the message distribution. A low-entropy, compact protocol is more efficient.2  
  * **Causal Influence of Communication (CIC):** A critical metric to prove that communication is not spurious but is causally impacting behavior. CIC measures the mutual information between a message sent by one agent and the subsequent action taken by the receiving agent, while controlling for the environmental state.2 This directly answers the question: "Does listening to a message actually change how an agent behaves?"  
  * **Interpretability Score:** Given the guided design, the interpretability of the protocol can be directly measured. This can be done through human evaluation, where participants are asked to guess the meaning of emergent symbols, or through automated methods that measure the alignment between the emergent symbols and the natural language concepts used for guidance.15  
  * **Zero-Shot Generalization (ZSC):** To test the robustness of the learned protocol, trained agents will be evaluated in ad-hoc teams. This involves pairing an agent with new teammates that were trained in a separate, independent run. Success in this ZSC setting demonstrates that the agents have learned a robust, shared convention rather than a brittle protocol co-adapted to their specific training partners.16

### **Future Research Trajectories**

The successful implementation of this PoC will open several avenues for future research, pushing towards more sophisticated and human-like communication.

* **Complex Linguistic Phenomena:** Future work could investigate the conditions required for the emergence of more complex linguistic structures, such as syntax (rules for combining symbols), recursion (embedding structures within each other), and deixis (the ability to refer to things relative to the context, like "here," "now," or "that one").39 These are active frontiers in emergent communication research.  
* **Advanced Dialogue Structures:** The PoC can be extended to explore more complex communication topologies and dialogue patterns. This includes one-to-many communication, where a single speaker broadcasts to multiple listeners with potentially different interests, and its effect on the emergence of compositionality.27 Deepening the capacity for contextual, multi-turn dialogue is another key direction.35  
* **Human-in-the-Loop Learning and Teaming:** A significant future goal is to enable agents to learn and refine their communication protocols through direct interaction with human users. This would involve developing methods for agents to learn from human feedback, clarification requests, and instructions, paving the way for true human-agent teaming where the AI can adapt its communicative style to its human partner.12

## **Conclusion**

This report has conducted an exhaustive investigation into the development of emergent communication protocols for multi-agent systems. The analysis reveals a critical trade-off at the heart of the field: **fully emergent protocols**, while theoretically capable of achieving maximal task-specific optimization, are practically hindered by severe challenges in training stability, interpretability, and generalization. In contrast, the **guided evolution** paradigm provides a suite of robust engineering solutions to these problems, enabling the development of stable, effective, and understandable communication systems.

The proposed PoC design embodies the principles of guided evolution. By using a CTDE architecture and grounding the emergent protocol in natural language via an LLM-based auxiliary reward, the design directly confronts the primary challenges of MARL. This approach promises not only to achieve high performance on collaborative tasks but also to produce a communication system that is stable to train, interpretable for analysis and debugging, generalizable to new partners and tasks, and fundamentally safer from a governance and security standpoint.

Therefore, the final recommendation of this research is to proceed with the development of the PoC based on the **guided evolution** paradigm. This strategy represents the most pragmatic and powerful path toward realizing the strategic goal of creating sophisticated, collaborative AI agents that can communicate effectively and flexibly, providing a solid and extensible foundation for future innovation in multi-agent systems.

#### **Works cited**

1. Emergent Communication in Multi-Agent Reinforcement Learning for Future Wireless Networks \- OuluREPO, accessed on June 16, 2025, [https://oulurepo.oulu.fi/bitstream/handle/10024/53991/nbnfioulu-202502061482.pdf?sequence=1\&isAllowed=y](https://oulurepo.oulu.fi/bitstream/handle/10024/53991/nbnfioulu-202502061482.pdf?sequence=1&isAllowed=y)  
2. On the Pitfalls of Measuring Emergent Communication \- arXiv, accessed on June 16, 2025, [https://arxiv.org/pdf/1903.05168](https://arxiv.org/pdf/1903.05168)  
3. COMMUNICATION IN MULTI-AGENT REINFORCEMENT LEARNING: INTENTION SHARING \- OpenReview, accessed on June 16, 2025, [https://openreview.net/pdf?id=qpsl2dR9twy](https://openreview.net/pdf?id=qpsl2dR9twy)  
4. Biases for Emergent Communication in Multi-agent Reinforcement Learning, accessed on June 16, 2025, [http://papers.neurips.cc/paper/9470-biases-for-emergent-communication-in-multi-agent-reinforcement-learning.pdf](http://papers.neurips.cc/paper/9470-biases-for-emergent-communication-in-multi-agent-reinforcement-learning.pdf)  
5. (PDF) A survey of multi-agent deep reinforcement learning with ..., accessed on June 16, 2025, [https://www.researchgate.net/publication/377208188\_A\_survey\_of\_multi-agent\_deep\_reinforcement\_learning\_with\_communication](https://www.researchgate.net/publication/377208188_A_survey_of_multi-agent_deep_reinforcement_learning_with_communication)  
6. MARL \- CommRL, accessed on June 16, 2025, [https://commrl-docs.readthedocs.io/en/latest/intro/MARL/](https://commrl-docs.readthedocs.io/en/latest/intro/MARL/)  
7. Multi-agent Reinforcement Learning: A Comprehensive Survey \- arXiv, accessed on June 16, 2025, [https://arxiv.org/pdf/2312.10256](https://arxiv.org/pdf/2312.10256)  
8. Reward-Independent Messaging for Decentralized Multi-Agent Reinforcement Learning \- arXiv, accessed on June 16, 2025, [https://arxiv.org/html/2505.21985v1](https://arxiv.org/html/2505.21985v1)  
9. An Inductive Bias for Emergent Communication in a Continuous Setting Abstract 1 Introduction 2 Positive Signaling, accessed on June 16, 2025, [https://proceedings.mlr.press/v233/villanger24a/villanger24a.pdf](https://proceedings.mlr.press/v233/villanger24a/villanger24a.pdf)  
10. Reviews: Learning to Communicate with Deep Multi-Agent Reinforcement Learning \- NIPS, accessed on June 16, 2025, [https://proceedings.neurips.cc/paper/2016/file/c7635bfd99248a2cdef8249ef7bfbef4-Reviews.html](https://proceedings.neurips.cc/paper/2016/file/c7635bfd99248a2cdef8249ef7bfbef4-Reviews.html)  
11. Learning to Communicate with Deep Multi-Agent Reinforcement ..., accessed on June 16, 2025, [https://papers.nips.cc/paper/6042-learning-to-communicate-with-deep-multi-agent-reinforcement-learning](https://papers.nips.cc/paper/6042-learning-to-communicate-with-deep-multi-agent-reinforcement-learning)  
12. Pow-Wow: A Dataset and Study on Collaborative ... \- TTIC, accessed on June 16, 2025, [https://ttic.edu/ripl/assets/publications/yoneda20.pdf](https://ttic.edu/ripl/assets/publications/yoneda20.pdf)  
13. Emergent Language-Based Coordination In Deep ... \- ACL Anthology, accessed on June 16, 2025, [https://aclanthology.org/2022.emnlp-tutorials.3.pdf](https://aclanthology.org/2022.emnlp-tutorials.3.pdf)  
14. Towards Language-Augmented Multi-Agent Deep Reinforcement Learning \- arXiv, accessed on June 16, 2025, [https://arxiv.org/html/2506.05236v1](https://arxiv.org/html/2506.05236v1)  
15. Unsupervised Translation of Emergent Communication, accessed on June 16, 2025, [https://ojs.aaai.org/index.php/AAAI/article/view/34489/36644](https://ojs.aaai.org/index.php/AAAI/article/view/34489/36644)  
16. NeurIPS Poster Language Grounded Multi-agent Reinforcement Learning with Human-interpretable Communication, accessed on June 16, 2025, [https://neurips.cc/virtual/2024/poster/96086](https://neurips.cc/virtual/2024/poster/96086)  
17. Learning Translations: Emergent Communication Pretraining ... \- IJCAI, accessed on June 16, 2025, [https://www.ijcai.org/proceedings/2024/0005.pdf](https://www.ijcai.org/proceedings/2024/0005.pdf)  
18. Learning Translations: Emergent Communication Pretraining for Cooperative Language Acquisition \- arXiv, accessed on June 16, 2025, [https://arxiv.org/html/2402.16247v1](https://arxiv.org/html/2402.16247v1)  
19. Learning to request guidance in emergent language \- ACL Anthology, accessed on June 16, 2025, [https://aclanthology.org/D19-6407.pdf](https://aclanthology.org/D19-6407.pdf)  
20. Towards Human-Like Emergent Communication via Utility, Informativeness, and Complexity, accessed on June 16, 2025, [https://direct.mit.edu/opmi/article/doi/10.1162/opmi\_a\_00188/128779/Towards-Human-Like-Emergent-Communication-via](https://direct.mit.edu/opmi/article/doi/10.1162/opmi_a_00188/128779/Towards-Human-Like-Emergent-Communication-via)  
21. On the Role of Emergent Communication for Social Learning ... \- arXiv, accessed on June 16, 2025, [https://arxiv.org/abs/2302.14276](https://arxiv.org/abs/2302.14276)  
22. Learning Multi-Agent Communication with Contrastive Learning ..., accessed on June 16, 2025, [https://openreview.net/forum?id=vZZ4hhniJU](https://openreview.net/forum?id=vZZ4hhniJU)  
23. Language Grounded Multi-agent Reinforcement Learning with Human-interpretable Communication | OpenReview, accessed on June 16, 2025, [https://openreview.net/forum?id=DUHX779C5q\&referrer=%5Bthe%20profile%20of%20Behdad%20Chalaki%5D(%2Fprofile%3Fid%3D\~Behdad\_Chalaki1)](https://openreview.net/forum?id=DUHX779C5q&referrer=%5Bthe+profile+of+Behdad+Chalaki%5D\(/profile?id%3D~Behdad_Chalaki1\))  
24. Emergent Corpus Pretraining Benefits Vision Language Modeling ..., accessed on June 16, 2025, [https://openreview.net/forum?id=vSkcS3qnZk](https://openreview.net/forum?id=vSkcS3qnZk)  
25. Reviews: Learning Multiagent Communication with Backpropagation \- NIPS papers, accessed on June 16, 2025, [https://papers.nips.cc/paper\_files/paper/2016/file/55b1927fdafef39c48e5b73b5d61ea60-Reviews.html](https://papers.nips.cc/paper_files/paper/2016/file/55b1927fdafef39c48e5b73b5d61ea60-Reviews.html)  
26. Concept-Best-Matching: Evaluating Compositionality in Emergent Communication \- arXiv, accessed on June 16, 2025, [https://arxiv.org/abs/2403.14705](https://arxiv.org/abs/2403.14705)  
27. One-to-Many Communication and Compositionality in Emergent ..., accessed on June 16, 2025, [https://aclanthology.org/2024.emnlp-main.1157/](https://aclanthology.org/2024.emnlp-main.1157/)  
28. Emergent Communication Protocols in Multi-Agent Systems: How Do AI Agents Develop Their Languages? \- ResearchGate, accessed on June 16, 2025, [https://www.researchgate.net/publication/388103504\_Emergent\_Communication\_Protocols\_in\_Multi-Agent\_Systems\_How\_Do\_AI\_Agents\_Develop\_Their\_Languages](https://www.researchgate.net/publication/388103504_Emergent_Communication_Protocols_in_Multi-Agent_Systems_How_Do_AI_Agents_Develop_Their_Languages)  
29. A Review of the Applications of Deep Learning-Based Emergent ..., accessed on June 16, 2025, [https://openreview.net/forum?id=jesKcQxQ7j](https://openreview.net/forum?id=jesKcQxQ7j)  
30. Language games meet multi-agent reinforcement learning: A case ..., accessed on June 16, 2025, [https://academic.oup.com/jole/article/7/2/213/7128304](https://academic.oup.com/jole/article/7/2/213/7128304)  
31. Dynamics of the MARL-based naming game experiment, with ten agents communicating about ten objects. \- ResearchGate, accessed on June 16, 2025, [https://www.researchgate.net/figure/Dynamics-of-the-MARL-based-naming-game-experiment-with-ten-agents-communicating-about\_fig3\_370112849](https://www.researchgate.net/figure/Dynamics-of-the-MARL-based-naming-game-experiment-with-ten-agents-communicating-about_fig3_370112849)  
32. Learning to communicate | OpenAI, accessed on June 16, 2025, [https://openai.com/index/learning-to-communicate/](https://openai.com/index/learning-to-communicate/)  
33. (PDF) The Enforcers: Consistent Sparse-Discrete Methods for ..., accessed on June 16, 2025, [https://www.researchgate.net/publication/357953323\_The\_Enforcers\_Consistent\_Sparse-Discrete\_Methods\_for\_Constraining\_Informative\_Emergent\_Communication](https://www.researchgate.net/publication/357953323_The_Enforcers_Consistent_Sparse-Discrete_Methods_for_Constraining_Informative_Emergent_Communication)  
34. Interpretable Learned Emergent Communication for Human-Agent Teams \- arXiv, accessed on June 16, 2025, [https://arxiv.org/pdf/2201.07452](https://arxiv.org/pdf/2201.07452)  
35. Emergent Language based Dialog for Collaborative Multi-agent ..., accessed on June 16, 2025, [https://openreview.net/forum?id=WsHaBoucSG](https://openreview.net/forum?id=WsHaBoucSG)  
36. Reviews: Learning Attentional Communication for Multi-Agent Cooperation \- NIPS, accessed on June 16, 2025, [https://proceedings.neurips.cc/paper/2018/file/6a8018b3a00b69c008601b8becae392b-Reviews.html](https://proceedings.neurips.cc/paper/2018/file/6a8018b3a00b69c008601b8becae392b-Reviews.html)  
37. Learning Multi-Agent Communication through Structured Attentive Reasoning \- NIPS, accessed on June 16, 2025, [https://papers.nips.cc/paper/2020/hash/72ab54f9b8c11fae5b923d7f854ef06a-Abstract.html](https://papers.nips.cc/paper/2020/hash/72ab54f9b8c11fae5b923d7f854ef06a-Abstract.html)  
38. AI Agent Communication: Breakthrough or Security Nightmare? \- Deepak Gupta, accessed on June 16, 2025, [https://guptadeepak.com/when-ai-agents-start-whispering-the-double-edged-sword-of-autonomous-agent-communication/](https://guptadeepak.com/when-ai-agents-start-whispering-the-double-edged-sword-of-autonomous-agent-communication/)  
39. NeurIPS Poster Speaking Your Language: Spatial Relationships in ..., accessed on June 16, 2025, [https://neurips.cc/virtual/2024/poster/93209](https://neurips.cc/virtual/2024/poster/93209)  
40. Temporal Dynamics in Emergent Communication \- ePrints Soton \- University of Southampton, accessed on June 16, 2025, [https://eprints.soton.ac.uk/498258/1/Olaf\_Lipinski\_PhD\_Thesis.pdf](https://eprints.soton.ac.uk/498258/1/Olaf_Lipinski_PhD_Thesis.pdf)
