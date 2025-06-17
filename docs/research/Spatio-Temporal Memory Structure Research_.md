

# **Technical Specification P4-18: A Spatio-Temporal Bitemporal Graph Model for Advanced LTM**

## **Foundations of Dynamic Knowledge Representation**

The evolution of intelligent systems necessitates a transition from static repositories of facts to dynamic memory structures capable of representing, tracking, and reasoning about information that changes over time and varies with context. The current Long-Term Memory (LTM) design, which treats facts as immutable statements, is insufficient for nuanced reasoning about the world's dynamic nature. This section establishes the theoretical foundations for a new LTM, drawing from extensive research in temporal knowledge graphs, bitemporal data modeling, and event-centric representation to justify a paradigm shift.

### **1.1. From Static Facts to Temporal Knowledge**

Traditional Knowledge Graphs (KGs) have proven highly effective for representing structured knowledge and enhancing downstream applications like search and question answering.1 They model the world as a collection of facts, typically represented as triples in the form of

(subject, relation, object) or (head, relation, tail).3 However, this model inherently assumes that facts are static and perpetually true, disregarding their evolution over time.1 This limitation is significant, as a vast amount of real-world knowledge is valid only within a specific period.1 Without a temporal dimension, a knowledge base rapidly becomes outdated and its facts invalid, undermining its reliability and utility.4

To address this deficiency, the field has moved towards Temporal Knowledge Graphs (TKGs). A TKG incorporates time into the standard knowledge graph framework, fundamentally changing the representation of a fact from a triple to a quadruple: (subject, relation, object, timestamp), denoted as $(s, r, o, t)$.3 This timestamp,

$t$, can represent a discrete point in time (e.g., a specific date) or a continuous interval $\[t\_b, t\_e\]$ during which the fact holds true.3 The central challenge and primary focus of TKG research is the effective integration of this temporal validity to accurately capture the dynamics of entities and their relationships as they evolve.7

While the $(s, r, o, t)$ quadruple model is a foundational concept in TKG literature, it represents a necessary but ultimately insufficient abstraction for the requirements of an advanced, production-grade LTM. The single temporal variable $t$ conflates multiple, distinct temporal concepts that are critical for nuanced reasoning. For instance, the blueprint objective to answer "What was the company's stock price before the acquisition?" requires distinguishing between *when the price was valid* and *when the system recorded that price*. A single timestamp cannot capture this distinction, nor can it adequately represent the rich contextual metadata (e.g., source, confidence) associated with an observation. Therefore, while the quadruple model serves as a crucial conceptual starting point, it must be deconstructed and expanded into a more sophisticated structure. This report will treat the simple TKG model as the academic baseline and build upon it to propose a production-ready data model that explicitly handles multiple temporal dimensions and rich contextual payloads.

### **1.2. The Bitemporal Imperative: Valid Time vs. Transaction Time**

To overcome the ambiguity of a single time axis, the proposed LTM must adopt a bitemporal data model. A temporal database can be uni-temporal (one time axis), bitemporal (two time axes), or even tri-temporal.9 Bitemporal modeling is a specific and powerful technique designed to manage historical data along two distinct timelines 10:

1. **Valid Time (Tv​):** This represents the time when a fact is true in the real world. It is also referred to as "application time" or "intrinsic time" because it is intrinsic to the fact itself.11 For example, the valid time for a CEO's tenure is the period from their start date to their end date. Valid time is user-supplied and can be corrected.  
2. **Transaction Time (Tt​):** This represents the time when a fact is recorded, updated, or logically deleted in the database. It is also known as "system time" or "extrinsic time".11 Transaction time is system-maintained, monotonically increasing, and cannot be changed.

This dual-axis approach is essential for applications requiring a complete and verifiable audit trail, such as financial reporting or regulatory compliance.10 Its fundamental principle is

**data immutability**: data is never physically overwritten or deleted.10 Instead, a change is recorded by closing the transaction time interval of the old version and inserting a new version with a new transaction time start, preserving the full history of what was known and when.15 This capability is critical in dynamic graph analytics, where information about events may arrive late or out of order, and the system must be able to reconstruct states based on what it knew at a specific point in the past.11

The necessity of bitemporality is not merely theoretical; it is a non-negotiable prerequisite for fulfilling the LTM's core use cases. The blueprint's query, "What was the company's stock price before the acquisition?", can be interpreted in two fundamentally different ways that only a bitemporal system can disambiguate:

* **Historical Query (Querying on Valid Time):** "Using all the information the LTM possesses *today*, what was the stock price on the day before the acquisition?" This query fixes the transaction time to now and seeks a specific point in the *valid time* axis.  
* **Audit Query (Querying on Valid and Transaction Time):** "Rewind the LTM's state to the day before the acquisition. Based on the information the system *knew at that moment*, what did it believe the stock price was?" This query seeks a specific point in both the *valid time* and *transaction time* axes.

The ability to answer both types of questions is crucial for understanding not only historical reality but also the rationale behind past decisions, which may have been based on data that was subsequently corrected or updated.11 Therefore, any proposed data model or API for the LTM that supports only a single time axis (uni-temporal) would be fundamentally incapable of meeting the system's specified objectives. Bitemporality must be a primary design constraint.

### **1.3. Modeling Paradigms: Event-Centric vs. Fact-Centric**

Within the broader landscape of temporal graphs, two primary modeling paradigms emerge: fact-centric and event-centric. The conventional TKG model is **fact-centric**, extending the static $(s, r, o)$ triple with a temporal component to form a quadruple.3 This approach excels at representing states and attributes that persist over time, such as a person's date of birth or a company's headquarters.

An alternative and increasingly popular paradigm is the **Event-Centric Knowledge Graph (ECKG)**.16 In an ECKG, the "event" itself is promoted to a first-class entity in the graph.16 Instead of directly connecting two entities with a timestamped edge, an

Event node is created. This node is then linked to participants (agents), a location, a time, and other contextual properties.19 This represents a significant shift from modeling static master data to handling dynamic transactional data.16 For example, to model a financial transaction, a fact-centric approach might create a

(payer)-\[paid {amount, time}\]-\>(payee) relationship. An event-centric approach would create an (event:Transaction) node and link it to the payer, payee, amount, and time: (payer)\<--(event:Transaction)--\>(payee), (event)--\>(amount), (event)--\>(time). This structure is inherently better at capturing the rich, multi-faceted context of a dynamic occurrence.16

A purely fact-centric model struggles to elegantly represent the complex context of an event. Modeling "Company A acquired Company B for $1B on Jan 1, 2023, announced by CEO C" would require a series of disconnected or awkwardly modeled temporal facts. Conversely, a purely event-centric model can be verbose for representing simple, stable facts like "Paris is the capital of France." The LTM must be capable of storing both long-lived, stable knowledge and discrete, dynamic events with equal facility.

Therefore, the optimal design is not a rigid choice between these two paradigms but a **hybrid model**. The proposed LTM will use a standard property graph structure for representing entities and their relatively static attributes, aligning with the fact-centric approach. However, when a complex, dynamic interaction needs to be recorded, the model will employ an event-centric pattern by creating an Event node. This Event node serves as a reified representation of the interaction, linking to all participating entities and containing the rich spatio-temporal and contextual metadata. This hybrid strategy leverages the conciseness of the fact-centric model for stable knowledge and the expressive power of the event-centric model for dynamic occurrences, providing a flexible and comprehensive framework. This approach aligns with advanced concepts like the Meta-Property Graph, where a complex relationship (the event) can be reified into a node to be described with its own properties.21

## **A Bitemporal Property Graph Model for the LTM**

This section presents the detailed technical specification for the new LTM data model. Building on the foundational principles of bitemporality and a hybrid fact/event-centric approach, we define the **Bitemporal Property Graph Model (BPGM)**. This model extends the existing P3-15 property graph schema to natively support versioned, contextualized facts, providing a robust and scalable foundation for the next-generation LTM.

### **2.1. Proposed Schema: The Bitemporal Property Graph Model (BPGM)**

The standard Property Graph Model (PGM) annotates nodes and edges with simple key-value pairs.12 Naive temporal extensions that simply add a timestamp to a node or edge suffer from a critical flaw: when any single property of an element changes, the entire element (node or edge) must be logically duplicated to record the new state. This leads to massive data redundancy and significant storage and processing overhead, especially for entities with frequently changing properties.12

The solution, inspired by advanced models like the Temporal Property Graph Model Plus (TPGM+), is to move the bitemporal versioning from the element level down to the **property level**.12 This architectural choice is the cornerstone of the BPGM. It elegantly separates the persistent identity of an entity from its time-varying state. In the BPGM, a node like

(Person {id: 123}) represents the immutable identity of an individual across all time. The attributes of this person, such as their address or job title, are not stored as static key-value pairs on the node itself. Instead, they are represented as a history of versioned states attached to that identity.

We formally define the BPGM schema as follows:

* **Nodes and Relationships:** Nodes and relationships serve as anchors for identity. They possess a unique identifier but do not have inherent temporal properties at the top level. For example, a node is simply (c:Company {entity\_id: 'acme\_inc'}).  
* **Properties:** A property on a node or relationship is no longer a single key-value pair. It is a key associated with a **list of versioned value objects**. Each object in this list represents a distinct state of that property over time and is structured to capture full bitemporal and contextual information.

The structure of a versioned value object within a property's list is:

{value: \<The property’s value\>,valid\_from: \<Timestamp\>,valid\_to: \<Timestamp\>,transaction: \<Transaction Object\>}  
This model ensures that the history of every property is preserved immutably. When a property changes, a new version object is appended to the list, and the transaction object of the previous version is updated to reflect that it has been superseded. This approach prevents data duplication and provides a complete, auditable history at the most granular level possible.

### **2.2. Extending the P3-15 Semantic Graph Schema**

The transition to the BPGM is an extension, not a replacement, of the existing P3-15 schema. The flexibility of the property graph model allows for this evolution without disrupting the core conceptual model of entities and relationships that developers are familiar with.23

The transformation is applied as follows:

* **Node Transformation:** A simple node from the P3-15 schema, such as (c:Company {name: 'Acme Inc.', stock\_price: 150}), is transformed in the BPGM. The identity is preserved, but the volatile properties are moved into versioned lists.  
  * **Identity Node:** (c:Company {entity\_id: 'acme\_inc'})  
  * **Versioned Properties:**  
    * c.name \=  
    * c.stock\_price \=  
* **Relationship Transformation:** A relationship, such as (c)--\>(p), also has its existence and properties versioned. While the relationship itself connects the two identity nodes, its validity over time is captured by a bitemporal property attached to it.  
  * **Relationship:** (c)--\>(p)  
  * **Versioned Property on Relationship:** r.status \=

Example Application:  
Let us revisit the blueprint query: "What was the company's stock price before the acquisition?" Assume the acquisition event occurred on 2023-03-31.

* **Node States:**  
  * Node: (stock:Stock {ticker: 'ACME'})  
  * Property stock.price:  
    JSON  
    \[  
      { "value": 100, "valid\_from": "2022-01-01Z", "valid\_to": "2022-12-31Z",... },  
      { "value": 120, "valid\_from": "2023-01-01Z", "valid\_to": "2023-03-31Z",... },  
      { "value": 150, "valid\_from": "2023-04-01Z", "valid\_to": "infinity",... }  
    \]

* **Event Node:** An Event node would represent the acquisition: (event:Event {type: 'Acquisition'}). This event node would have its own versioned property event.date \= \[{value: '2023-03-31Z',...}\].  
* **Query Logic:** A query would first retrieve the date of the acquisition event. Then, it would search the stock.price property history for the version whose valid\_to timestamp matches the acquisition date, thus retrieving the value of 120\.

### **2.3. Modeling Context: Spatial and Conceptual Dimensions**

A truly advanced LTM must capture not only *when* a fact is true, but also *where* it is true and *how* the system came to know it. The BPGM is designed to be extensible for this rich contextual information.25

* **Spatial Context:** Spatio-temporal data possesses both a geographic and a temporal dimension.26 For entities that have a physical location, we introduce a  
  location property. This property is versioned bitemporally just like any other, allowing the LTM to track an entity's movement over time. The value of the location property should be a structured object, such as a GeoJSON representation or a native Point data type if supported by the graph database.28  
  * Example: person.location \= \[ { value: {type: 'Point', coordinates: \[-118.24, 34.05\]}, valid\_from: '2020-01-01Z',... },... \]  
* **Conceptual Context:** Metadata such as the source document, the confidence score from an extraction model, or the specific NLP pipeline version used are critical for assessing data quality and lineage. This information answers the "how" and "why" behind a fact. It is crucial to recognize that this transactional metadata is orthogonal to the bitemporal validity of the fact itself. The valid\_from/valid\_to timestamps describe the fact's lifetime in the real world, while the transactional metadata describes the observation event.

To model this cleanly, we refine the BPGM structure by formalizing the transaction object within each versioned property value:

transaction={tx\_id: \<UUID\>,tx\_timestamp: \<Timestamp\>,source\_id: \<string\>,confidence: \<float\>,...other metadata}  
This design creates a clear separation of concerns. The bitemporal timestamps manage the two time axes, while the transaction object encapsulates all metadata related to the recording of that specific version. This structure makes it straightforward to execute powerful contextual queries, such as "retrieve all facts derived from source\_id: 'doc-456'" or "show all facts with a confidence below 0.75," without complicating the primary temporal logic. This moves the LTM towards the advanced capabilities of a Meta-Property Graph, where metadata is treated as a first-class, queryable citizen.21

### **2.4. Design Alternatives and Justification: Reification vs. Direct Annotation**

A key design decision in any temporal graph is how to attach properties, such as timestamps, to relationships. The BPGM's approach of adding versioned properties directly to edges is a form of **direct annotation**. An alternative, common in the RDF world, is **reification**.30 Reification involves creating an intermediate node to represent an instance of a statement, and then attaching properties to that new node. For example, to add a date to

(Alice)--\>(Bob), one would create a (stmt:Statement) node and add triples like (stmt, rdf:subject, :Alice), (stmt, rdf:predicate, :MARRIED\_TO), (stmt, rdf:object, :Bob), and finally (stmt, :onDate, "2022-05-10").

While RDF-star (RDF\*) provides a more compact syntax for this (\<\<:Alice :MARRIED\_TO :Bob\>\> :onDate "2022-05-10") 30, the underlying model still introduces a level of indirection. The BPGM deliberately rejects this pattern for property versioning for several reasons:

1. **Performance:** Benchmarks comparing property graph models with RDF-reification models for temporal workloads show a significant performance advantage for property graphs. For complex read queries, which are central to the LTM's function, property graph databases can be 4 to 10 times faster.32 The overhead of traversing and joining through intermediate reification nodes is a major performance bottleneck that is unacceptable for a high-throughput system.  
2. **Model Simplicity and Intuitiveness:** The property graph model is designed to be an intuitive representation of a domain, where what you draw on a whiteboard is what you store.23 Reification introduces a large number of structural nodes that do not correspond to real-world entities, complicating the graph structure and increasing the cognitive load for developers writing queries.31 The BPGM maintains a clean core graph of entities and their direct relationships, pushing the temporal complexity into the property data structures, which is a more manageable and encapsulated form of complexity.  
3. **Native Data Model Alignment:** The system's existing LTM is built on a property graph (P3-15). Extending this model with versioned properties is a natural evolution. Introducing a foreign modeling pattern like RDF reification would be architecturally inconsistent and add unnecessary friction.

It is important to clarify that while reification is rejected as a low-level mechanism for versioning properties, it is embraced as a high-level modeling choice for representing complex events, as described in Section 1.3. Creating an Event node to represent a multi-participant interaction like a corporate merger is a deliberate and powerful modeling decision, not a workaround for a data model limitation.

To provide a clear overview of these design trade-offs, the following table compares the BPGM against other temporal modeling approaches.

**Table 2.1: Comparison of Temporal Graph Modeling Approaches**

| Modeling Approach | Description | Expressiveness | Query Complexity | Performance (Read/Write) | Storage Overhead | Suitability for LTM |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **TKG Quadruple** | Extends (s,r,o) to (s,r,o,t).3 | Low. Cannot distinguish valid vs. transaction time. Poor context support. | Low for simple time points. High for intervals or complex context. | Varies by implementation. Model itself doesn't specify storage. | Low. Adds one field per fact. | **Unsuitable.** Fails to meet the core bitemporal requirement. |
| **Standard Reification** | Creates an intermediate node to represent a statement, allowing properties to be attached to it.30 | High. Can model bitemporality and rich context. | High. Queries require complex joins through statement nodes. | Poor. Significantly slower for complex reads than property graphs.32 | High. Adds multiple nodes and edges per annotated fact. | **Unsuitable.** Poor performance and high query complexity. |
| **RDF-star** | Syntactic sugar over reification for attaching properties to statements.30 | High. Same as reification. | Medium. Simpler syntax than standard reification but still requires reasoning about statements-about-statements. | Better than standard reification, but still generally slower than native property graphs.32 | Medium. More compact than standard reification. | **Not Recommended.** Less performant and less aligned with the incumbent property graph model. |
| **Event-Centric (Pure)** | Models events as first-class nodes, linked to participants, time, and place.16 | Very High. Excellent for dynamic, multi-faceted interactions. | Medium. Queries center around Event nodes. Can be verbose for simple static facts. | Good. Well-suited for transactional data. | High. Can be verbose for representing simple, persistent states. | **Partially Suitable.** Excellent for dynamic data but not ideal as the sole model. Best used in a hybrid approach. |
| **BPGM (Proposed)** | Attaches versioned, bitemporal property lists directly to nodes and edges.12 | Very High. Natively supports bitemporality and rich transactional context at the property level. | Medium. Requires querying into nested property structures but keeps graph topology clean. | **High.** Leverages native property graph performance. Avoids reification joins. Risk depends on indexing capability. | Medium. Adds overhead per property, but avoids duplicating entire nodes/edges. | **Highly Suitable.** Directly meets all requirements for bitemporality, context, and performance in a property graph-native way. |

## **LTM Service API v2: Specification for Temporal Queries**

The adoption of the Bitemporal Property Graph Model (BPGM) necessitates a corresponding evolution of the LTM Service API (P2-01). This section provides a detailed specification for version 2 of the API, designed to expose the full power of the temporal LTM to client applications in a clear, consistent, and backward-compatible manner.

### **3.1. Core Principles of a Temporal API**

The design of the LTM Service API v2 is guided by a set of core principles derived from best practices in temporal database systems.9

1. **Clarity and Explicitness:** The API must make a clear and unambiguous distinction between queries on valid time and queries on transaction time. This will be achieved through explicit, well-named query parameters.  
2. **Simplicity and Backward Compatibility:** The most common use case will remain querying the *current* state of the world. Therefore, API calls without any temporal parameters will default to this behavior, returning the state of the graph with the latest transaction time and a valid time of now. This ensures that existing client applications that are not temporally aware will continue to function without modification.  
3. **Optional Temporality:** All temporal query parameters will be optional. Their presence in a request signals the intent to perform a temporal query; their absence signals a standard, current-state query. This prevents unnecessary complexity for the majority of API calls.  
4. **Standardization:** All timestamp values used in request parameters and response bodies will adhere strictly to the ISO 8601 format to ensure consistency and interoperability.

### **3.2. Proposed Endpoint Modifications**

The existing CRUD (Create, Read, Update, Delete) operations of the LTM Service are redefined in the context of an immutable, bitemporal system.

* POST /api/v2/ltm/ingest: This endpoint will replace the separate create and update endpoints. When new information is ingested, the service will determine whether it's a new entity or a new version of an existing entity's property. It will then create a new versioned value object in the appropriate property list, setting its valid\_from and transaction details accordingly and updating the valid\_to and transaction of the previous version if necessary.  
* GET /api/v2/ltm/retrieve: This remains the primary query endpoint. It will be enhanced with a suite of optional temporal query parameters (detailed in Section 3.3) to allow for snapshot, range, and audit queries.  
* DELETE /api/v2/ltm/entity/{id}: In a bitemporal system, data is never physically deleted. A DELETE call to this endpoint will perform a **logical delete**. This operation sets the valid\_to timestamp of the current active version(s) of an entity's properties to the time of the request, effectively ending their validity in the real world. The transaction history remains intact for auditing.  
* GET /api/v2/ltm/history/{entity\_id}: This is a new, dedicated endpoint designed to retrieve the complete, ordered version history of all properties for a given entity. This is useful for client applications that need to visualize the evolution of an entity over time.

To provide an unambiguous contract for implementation, the following table formally specifies the API endpoints.

**Table 3.1: LTM Service API v2 Endpoint Specification**

| Endpoint & Method | Description | Path Parameters | Query Parameters | Request Body | Success Response |
| :---- | :---- | :---- | :---- | :---- | :---- |
| POST /api/v2/ltm/ingest | Ingests a new fact or a new version of a fact. The system handles bitemporal versioning automatically. | \- | \- | JSON object representing the fact, including its value and valid time. | 202 Accepted with transaction ID. |
| GET /api/v2/ltm/retrieve | Executes a graph query, with optional temporal constraints. Defaults to current state. | \- | query (string, required): The graph query (e.g., Cypher). valid\_at (string, optional): ISO 8601 timestamp for a valid time snapshot. transaction\_at (string, optional): ISO 8601 timestamp for an audit snapshot (requires valid\_at). valid\_from (string, optional): Start of a valid time range query. valid\_to (string, optional): End of a valid time range query. | \- | 200 OK with JSON array of query results. |
| DELETE /api/v2/ltm/entity/{id} | Performs a logical delete by setting the valid\_to timestamp of the entity's current state to now. | id (string): The unique ID of the entity to logically delete. | \- | \- | 200 OK with transaction ID. |
| GET /api/v2/ltm/history/{id} | Retrieves the full bitemporal history for all properties of a specific entity. | id (string): The unique ID of the entity. | \- | \- | 200 OK with a JSON object containing the full versioned property lists. |

### **3.3. Query Parameter Specification**

The power of the temporal LTM is unlocked through the query parameters for the GET /retrieve endpoint. These parameters are designed to be composable and map directly to the fundamental types of temporal queries. Their design is influenced by temporal query language constructs like T-Cypher's SNAPSHOT and RANGE\_SLICE clauses 34 and function-based extensions seen in systems like Drasi.36

* query=\<string\>: (Required) The graph pattern matching query (e.g., in Cypher syntax) to be executed. The query is written against the logical graph structure, without needing to specify the temporal logic, which is handled by the other parameters.  
* valid\_at=\<timestamp\>: (Optional) Specifies a single point in **valid time**. The LTM will resolve the query against the state of the graph as it was in the real world at that exact moment. This is a "snapshot" query.  
* transaction\_at=\<timestamp\>: (Optional) Specifies a single point in **transaction time**. This parameter can only be used in conjunction with valid\_at. It instructs the LTM to first travel back to the specified transaction time and then, using only the data available at that point, resolve the query for the given valid\_at time. This is an "audit" query.  
* valid\_from=\<timestamp\> & valid\_to=\<timestamp\>: (Optional) Specifies an interval in **valid time**. The LTM will return all versions of facts that were valid at any point during this interval. This is a "range" or "slice" query, useful for finding all changes within a period.

If no temporal parameters are supplied, the system defaults to valid\_at=now and the latest transaction time, providing the most current view of the data.

### **3.4. Example Queries and Responses**

To illustrate the API's functionality, consider the following use cases.

**Use Case 1: Historical Query**

* **Question:** "What was the company's stock price on March 30th, 2023?"  
* **API Call:**  
  HTTP  
  GET /api/v2/ltm/retrieve?query=MATCH (c:Company {name:'Acme Inc.'})--\>(s:Stock) RETURN s.price\&valid\_at=2023-03-30T23:59:59Z

* **Logic:** The LTM service receives the request. It finds the s.price property and searches its version list for the object where valid\_from \<= '2023-03-30...' and valid\_to \> '2023-03-30...'. It uses the latest transaction time by default.  
* **Expected Response:**  
  JSON  
  {  
    "results":  
  }

**Use Case 2: Audit Query**

* **Question:** "On January 15th, 2023, what did we think the stock price was for January 10th, 2023?"  
* **API Call:**  
  HTTP  
  GET /api/v2/ltm/retrieve?query=...\&valid\_at=2023-01-10T12:00:00Z\&transaction\_at=2023-01-15T12:00:00Z

* **Logic:** The LTM service first filters the entire database to a view containing only transactions that occurred on or before 2023-01-15. Within that historical view of the database, it then performs the valid time snapshot query for 2023-01-10.  
* **Expected Response:** The response structure is identical to the one above, but the value returned would be based on the information available to the system on Jan 15th, which might be different from what is known today due to subsequent corrections or data loads.

## **Automating Temporal Context Extraction in the MemoryManager**

The value of the Bitemporal Property Graph Model is contingent on the ability to populate it with rich, structured data. This requires a significant enhancement of the MemoryManager (P3-16) and its ingestion pipeline. The goal is to automate the extraction of temporal and contextual metadata from unstructured text, transforming raw documents into the structured, versioned facts required by the BPGM. This process involves a sophisticated, multi-stage Natural Language Processing (NLP) pipeline.17

### **4.1. NLP Pipeline for Temporal Awareness**

The existing MemoryManager ingestion process will be augmented to include a series of specialized NLP tasks. The output of this pipeline will be a structured representation of the information in the source text, ready to be mapped into the BPGM. The quality and granularity of the LTM are directly determined by the capabilities of this pipeline; if context is not extracted here, it cannot be queried later.

The proposed pipeline consists of the following sequential stages:

1. **Text Preprocessing:** The initial step involves cleaning and preparing the raw text. This includes standard procedures like tokenization (splitting text into words and punctuation) and Part-of-Speech (POS) tagging (assigning grammatical roles like noun, verb, adjective to each token).39  
2. **Named Entity Recognition (NER):** This stage identifies and classifies key entities within the text, such as people, organizations, and locations.39  
3. **Temporal Expression Extraction (TEE):** A specialized form of NER, this stage identifies all phrases and words that refer to time, dates, or durations.42  
4. **Temporal Normalization:** This crucial stage converts the extracted temporal expressions, which are often relative or ambiguous, into a standardized, absolute format (ISO 8601).42  
5. **Event and Relation Extraction:** This stage moves beyond identifying individual entities to understanding the relationships between them. It identifies actions (events) and links the participating entities, along with their temporal and spatial context, into structured facts.44  
6. **Graph Population:** The final stage maps the structured facts extracted by the pipeline into the BPGM, creating or updating nodes, relationships, and their versioned properties.

### **4.2. Entity and Expression Extraction**

The foundation of the pipeline is the accurate identification of entities. This is accomplished using Named Entity Recognition (NER), a core NLP task.40 The MemoryManager will employ a state-of-the-art NER model, likely a fine-tuned Transformer-based architecture such as those available through libraries like Spark NLP or spaCy.40 The model must be capable of recognizing a range of entity types relevant to the LTM's domain.

* **Standard Entities:** PERSON, ORGANIZATION, GPE (Geo-Political Entity), LOCATION.  
* **Temporal Entities:** DATE, TIME, DURATION.

For example, given the input sentence: "Apple Inc. is planning to open a new office in San Francisco in March 2025," the NER module is expected to produce the following classified entities 39:

* ("Apple Inc.", "ORG")  
* ("San Francisco", "LOC")  
* ("March 2025", "DATE")

This step effectively identifies the "who," "what," and "where" of the text, along with the raw temporal expressions.

### **4.3. Temporal Normalization**

Temporal expressions in natural language are notoriously complex and varied. They can be absolute ("on April 1, 1976"), relative ("two weeks ago," "next Tuesday"), or durational ("for three years").42 The Temporal Normalization stage is responsible for resolving these expressions into a canonical format that can be stored in the database. This is a critical step for enabling computational reasoning over time.42

The normalization module will implement the following logic:

* It will take as input the temporal expressions identified by the TEE stage and a crucial piece of metadata: the **Document Creation Time (DCT)**. The DCT serves as the anchor point for resolving relative expressions.  
* Using a combination of rule-based logic (similar to systems like HeidelTime 43) and machine learning models, it will convert expressions into ISO 8601 timestamps or intervals.  
  * "March 2025" becomes the interval \[2025-03-01, 2025-03-31\].  
  * "yesterday" (relative to a DCT of 2024-10-27) becomes 2024-10-26.  
  * "two weeks after the accident" requires first normalizing the time of "the accident" and then adding a 14-day duration.  
* The output of this stage is a set of machine-readable timestamps ready for insertion into the valid\_from and valid\_to fields of the BPGM.

### **4.4. Event and Relation Extraction**

With entities identified and times normalized, the final extraction step is to determine how they are related. This is accomplished through Relation Extraction and the more advanced Event Extraction.44 While simple Relation Extraction might identify a

(born\_in) relationship between an entity and a location, Event Extraction aims to capture a complete scenario: "Who did What to Whom, Where, and When".45 This is essential for populating the rich, contextual event nodes in our hybrid model.

A supervised relation extraction model, trained on an annotated corpus like ACE 2005 or TACRED 44, will be applied to sentences containing tagged entities.

* **Input:** A sentence with pre-identified entities: is planning to open a new office in in.  
* **Model Logic:** The model identifies the verb "open" as an event trigger and recognizes the pattern of an organization opening something in a location at a specific time.  
* Structured Output: The model produces a structured fact, which can be represented as a tuple:  
  (subject: "Apple Inc.", relation: "opens\_office", object: "office", location: "San Francisco", time: "2025-03")

This structured output is the final product of the NLP pipeline. The MemoryManager's graph population module then takes this tuple and translates it into operations on the BPGM. It would ensure nodes for "Apple Inc." and "San Francisco" exist, create a relationship between them, and add a new versioned entry to the relevant property (e.g., AppleInc.offices) with the value "San Francisco" and the valid\_from set to 2025-03-01. The transaction object for this new version would contain metadata about this ingestion event, including the source document ID and the confidence score from the relation extraction model.

## **Feasibility and Performance Analysis**

The proposed Bitemporal Property Graph Model (BPGM) and its associated API and ingestion pipeline represent a significant architectural advancement. This section provides a critical analysis of the design's feasibility, evaluating its implications for storage, indexing, and query performance to ensure the system is not only powerful in theory but also practical and scalable in implementation.

### **5.1. Storage Architecture: Event Sourcing vs. Snapshotting**

The representation of temporal graphs can be broadly categorized into two approaches: event-based models and snapshot-based models.4 An event-based approach, often referred to as a Continuous-Time Dynamic Graph (CTDG), represents the graph as a continuous stream of change events (e.g., edge additions/deletions).48 This is conceptually similar to the

**event sourcing** pattern, where the state of an application is determined by replaying a log of immutable events.50 Its primary advantage is a perfect, auditable history. However, reconstructing the state of an entity with a long and active history can be computationally expensive, as it requires replaying a large number of events, which negatively impacts query latency.50

A snapshot-based approach, or Discrete-Time Dynamic Graph (DTDG), stores the complete state of the graph at discrete points in time.4 While this makes querying a specific historical state very fast (a simple lookup), it is often prohibitively expensive in terms of storage for large, frequently changing graphs.52 A compromise is the

**delta-based** approach, which stores periodic full snapshots (or "anchors") and the incremental changes (deltas) between them.53 To reconstruct a state, the system finds the nearest preceding snapshot and applies the subsequent deltas.

The proposed BPGM is inherently a delta-based model at the most granular level. The versioned list associated with each property is effectively an event log, or a series of deltas, for that specific attribute. This provides the full auditability of event sourcing. However, to mitigate the potential read-latency issues of a pure event-sourcing model, a **hybrid storage architecture** is recommended.

The primary storage mechanism will be the BPGM graph itself, as defined in Section 2\. To optimize read performance for historical queries, the system will implement a caching and materialization layer that creates and stores **snapshots** of frequently accessed or high-value entities. This aligns with the well-established pattern of using snapshots as a performance optimization in event-sourced systems 50 and with advanced temporal database designs like AeonG, which uses an "anchor-based" version retrieval technique to skip unnecessary traversals of historical versions.53 This hybrid strategy combines the storage efficiency and auditability of a granular, delta-based model with the read performance of a snapshot-based model.

### **5.2. Temporal Indexing Strategies**

The performance of any database system, particularly one handling complex temporal queries, is critically dependent on its indexing strategy.55 The BPGM, with its nested property structure, requires a careful and deliberate approach to indexing. The ability of the chosen graph database to support these specific indexing requirements is the single greatest technical risk to the project's success.

The following indexing strategy is proposed for the BPGM, to be validated in a proof-of-concept. This strategy draws on the capabilities of modern graph databases like Neo4j and JanusGraph, which support various index types including composite, range, text, and point indexes.56

1. **Entity Identity Index:** A unique composite index on the primary entity\_id property of all nodes is mandatory for fast, direct lookup of entities.  
2. **Temporal Range Indexes:** This is the most critical component for temporal query performance. The database *must* support the creation of **range indexes** on the valid\_from and valid\_to fields *within* the nested objects of the versioned property lists. Without this capability, any temporal query would degenerate into a full scan of an entity's entire property history, which is not scalable.  
3. **Transaction Time Index:** Similarly, a range index on the transaction.tx\_timestamp field is essential for performant audit queries.  
4. **Spatial Index:** For entities with geographic properties, a point or spatial index must be created on the location.value field to enable efficient spatial queries (e.g., "find all entities within this bounding box").56

The feasibility of this model hinges on the physical implementation details of the chosen graph database. Can it efficiently create and use an index on a field within a JSON array that is stored as a node property? If the database's indexing capabilities are limited to top-level properties, the BPGM as defined is not viable, and an alternative model (such as one that creates separate State nodes for each version) would be required, introducing its own performance trade-offs. Therefore, a proof-of-concept to validate the indexability of the BPGM is the highest-priority task in the implementation plan.

**Table 5.1: Indexing Strategy for Bitemporal Queries**

| Query Type | Example Cypher Snippet | Property to Index | Recommended Index Type | Expected Performance Impact |
| :---- | :---- | :---- | :---- | :---- |
| **Entity Lookup** | MATCH (c:Company {entity\_id: 'acme\_inc'}) | node.entity\_id | Unique Composite | **Critical.** Enables O(log N) lookup instead of O(N) scan. |
| **Current State Query** | ... WHERE p.valid\_to \= 'infinity' | property.valid\_to | Range | **High.** Speeds up finding the current version of a property. |
| **valid\_at Snapshot** | ... WHERE p.valid\_from \<= $ts AND p.valid\_to \> $ts | property.valid\_from, property.valid\_to | Range | **Critical.** The core index for all historical queries. Without it, temporal queries are infeasible. |
| **transaction\_at Audit** | ... WHERE t.tx\_timestamp \<= $tx\_ts | transaction.tx\_timestamp | Range | **Critical.** The core index for all audit queries. |
| **Time Range Query** | ... WHERE p.valid\_from \< $end AND p.valid\_to \> $start | property.valid\_from, property.valid\_to | Range | **High.** Speeds up queries that scan for all activity within a time window. |
| **Spatial Query** | ... WHERE point.withinBBox(n.location,...) | location.value | Point / Spatial | **Critical.** Essential for any location-based queries. |

### **5.3. Query Performance Evaluation**

The performance of queries against the BPGM will vary based on their complexity. A comprehensive performance evaluation, using a benchmark suite tailored to the LTM's expected workload, is a necessary step in the implementation process. The "Temporal Triangles" benchmark provides an excellent model for this, as it focuses on realistic, pattern-based queries with temporal constraints and measures latency, throughput, and resource usage.59

* **Snapshot Queries (valid\_at, transaction\_at):** Assuming the indexing strategy in 5.2 is successfully implemented, these queries should be highly performant. The query planner should be able to use the range indexes to perform an efficient index seek, directly locating the single correct version of each required property with minimal overhead.  
* **Range Queries (valid\_from, valid\_to):** These queries are inherently more expensive as they may retrieve multiple versions for each property within the specified time window. Performance will be a function of the time window's length and the data's volatility (i.e., how frequently properties change).  
* **Temporal Path Queries:** Queries that traverse paths across multiple entities and relationships, with temporal constraints on each step, will be the most computationally intensive. The query planner's ability to efficiently join the results from multiple indexed lookups on versioned properties will be paramount. This is a known hard problem, and performance will need to be carefully monitored and tuned.60 Query optimization techniques, including query rewriting and intelligent caching, will be essential.61

### **5.4. Implementation Complexity and Risks**

The transition to a bitemporal LTM is a complex undertaking with several identifiable risks that must be managed.

* **Data Migration:** Migrating the existing static graph to the BPGM is a significant one-time cost. A robust migration script must be developed to transform every property in the current graph into the new versioned list format. This script will need to assign an initial valid\_from and tx\_timestamp to all existing data, requiring careful planning to ensure data integrity.  
* **Query Complexity and Developer Training:** Writing queries against the BPGM is more complex than against a static graph. Developers will need to be trained on the new data model and the patterns for querying versioned properties. A simple MATCH (n) WHERE n.city \= 'SF' must be rewritten to correctly navigate the version list and apply temporal filters. This increases the cognitive load and potential for error. Well-documented helper functions and a library of query examples will be necessary to mitigate this.  
* **Database Capability Risk:** As emphasized throughout this section, the entire design is predicated on the underlying graph database's ability to efficiently index and query the nested data structures of the BPGM. This is the primary technical risk and must be retired early in the project via a proof-of-concept.  
* **Performance Tuning:** The hybrid storage model, with its caching and snapshotting layer, is not a "fire-and-forget" solution. It will require ongoing monitoring and tuning to define the right policies for which entities get snapshotted and how often, balancing read performance gains against the cost of snapshot creation and storage.

## **Recommendations and Implementation Roadmap**

This report has detailed the theoretical foundations, data model specification, API design, and feasibility analysis for transitioning the LTM to a spatio-temporal bitemporal system. This final section synthesizes these findings into a set of concrete recommendations and proposes a phased implementation plan designed to manage complexity and mitigate risk.

### **6.1. Final Specification Summary**

The analysis converges on a set of core recommendations that form the technical blueprint for the new LTM. The implementation of P4-18 should proceed based on the following specifications:

1. **Adopt the Bitemporal Property Graph Model (BPGM):** The LTM will be built upon the BPGM, as defined in Section 2\. This model versions individual properties on nodes and relationships, each with distinct valid time and transaction time dimensions, and encapsulates contextual metadata within a dedicated transaction object. This approach provides maximum expressiveness and auditability while aligning with the native property graph paradigm.  
2. **Implement the LTM Service API v2:** The LTM Service API will be updated to version 2, as specified in Section 3\. The new API will introduce optional temporal query parameters (valid\_at, transaction\_at, valid\_from, valid\_to) to the primary retrieve endpoint, ensuring backward compatibility while enabling powerful historical and audit queries.  
3. **Enhance the MemoryManager with an NLP Pipeline:** The MemoryManager will be augmented with the multi-stage NLP pipeline detailed in Section 4\. This pipeline is essential for automatically extracting and structuring temporal and contextual information from unstructured text, enabling the automated population of the BPGM.  
4. **Implement a Hybrid Storage and Caching Architecture:** The system will use the BPGM as its primary, event-sourced storage model. To ensure high read performance, this will be supplemented by a caching layer that periodically materializes and stores snapshots of frequently accessed or high-importance entities, as discussed in Section 5.1.

### **6.2. Phased Implementation Plan**

A phased approach is recommended to systematically de-risk and deliver this complex project. The plan prioritizes tackling the largest technical unknown first.

* **Phase 0: Proof of Concept (Duration: 1-2 Sprints)**  
  * **Objective:** Validate the single most critical technical assumption: the performance of the BPGM on the target graph database.  
  * **Key Tasks:**  
    1. Implement the BPGM schema for a small but representative subset of data.  
    2. Create the essential temporal and identity indexes as specified in Table 5.1.  
    3. Develop and execute a benchmark suite of core query patterns (snapshot, range, and simple path queries).  
  * **Exit Criteria:** Successful validation that the chosen database can index the nested property structure and that indexed snapshot queries achieve sub-millisecond latency under a representative load. A failure at this stage would necessitate a redesign of the core data model.  
* **Phase 1: Core Model and Uni-Temporal API (Duration: 1 Quarter)**  
  * **Objective:** Implement the foundational backend systems and enable historical querying (valid time).  
  * **Key Tasks:**  
    1. Full implementation of the BPGM storage logic.  
    2. Develop and test the data migration scripts to convert the existing LTM.  
    3. Implement the LTM Service API v2 endpoints (ingest, retrieve, delete, history).  
    4. Add support for the valid\_at, valid\_from, and valid\_to query parameters.  
  * **Exit Criteria:** A fully functional LTM capable of storing bitemporal data and serving historical queries against valid time.  
* **Phase 2: Bitemporal Capabilities and Performance Optimization (Duration: 1 Quarter)**  
  * **Objective:** Enable full bitemporal audit functionality and implement performance optimizations.  
  * **Key Tasks:**  
    1. Add support for the transaction\_at query parameter to enable audit queries.  
    2. Design and implement the hybrid snapshotting and caching layer to optimize read performance.  
    3. Build out the full functionality of the /history API endpoint.  
    4. Conduct large-scale performance and stress testing.  
  * **Exit Criteria:** The LTM meets all functional requirements of the bitemporal specification and satisfies performance SLAs.  
* **Phase 3: Automated Ingestion Pipeline (Duration: Ongoing)**  
  * **Objective:** Fully automate the population of the temporal LTM from unstructured sources.  
  * **Key Tasks:**  
    1. Incrementally develop, train, and integrate the NLP components from Section 4 (NER, TEE, Normalization, Relation Extraction).  
    2. Connect the output of the NLP pipeline to the ingest API endpoint.  
  * **Exit Criteria:** The MemoryManager can autonomously process new documents and correctly populate the LTM with versioned, contextualized facts.

### **6.3. Future Research Directions**

While the proposed specification provides a complete and robust system, it also serves as a foundation for future enhancements. Once the bitemporal LTM is established, several advanced research directions can be pursued:

* **Probabilistic and Fuzzy Time:** Real-world information is often temporally uncertain (e.g., "the event happened around 2010," "sometime last summer"). Future work could extend the BPGM to represent and query these fuzzy temporal statements, moving beyond precise timestamp intervals.  
* **Streaming Ingestion and Real-time Analytics:** The current design is focused on batch ingestion from documents. The next evolution would be to integrate with real-time data streams, enabling continuous updates and analysis on the temporal graph. This would involve leveraging frameworks for training and inference on dynamic graphs, such as TGL 63 or ETC.64  
* **Advanced Temporal Reasoning:** The specified LTM is primarily a retrieval system. The ultimate goal is to enable automated reasoning over its contents. This involves applying Temporal Knowledge Graph Completion (TKGC) and representation learning models to infer missing links, predict future events, and identify causal relationships within the temporal data.1 The rich, structured data produced by the BPGM will provide an ideal substrate for these advanced AI capabilities.

#### **Works cited**

1. \[2403.04782\] A Survey on Temporal Knowledge Graph: Representation Learning and Applications \- arXiv, accessed on June 17, 2025, [https://arxiv.org/abs/2403.04782](https://arxiv.org/abs/2403.04782)  
2. Knowledge Graphs \- Aidan Hogan, accessed on June 17, 2025, [https://aidanhogan.com/docs/knowledge-graphs-computing-surveys.pdf](https://aidanhogan.com/docs/knowledge-graphs-computing-surveys.pdf)  
3. A Brief Survey on Deep Learning-Based Temporal Knowledge Graph Completion \- MDPI, accessed on June 17, 2025, [https://www.mdpi.com/2076-3417/14/19/8871](https://www.mdpi.com/2076-3417/14/19/8871)  
4. A Survey on Temporal Knowledge Graph Embedding 1 introduction \- OpenReview, accessed on June 17, 2025, [https://openreview.net/pdf?id=Dmrcmt9izJO](https://openreview.net/pdf?id=Dmrcmt9izJO)  
5. A Survey on Temporal Knowledge Graph: Representation Learning and Applications \- arXiv, accessed on June 17, 2025, [https://arxiv.org/pdf/2403.04782](https://arxiv.org/pdf/2403.04782)  
6. A Survey on Temporal Knowledge Graph: Representation Learning and Applications \- arXiv, accessed on June 17, 2025, [https://arxiv.org/html/2403.04782v1](https://arxiv.org/html/2403.04782v1)  
7. Temporal Knowledge Graph Completion: A Survey \- IJCAI, accessed on June 17, 2025, [https://www.ijcai.org/proceedings/2023/0734.pdf](https://www.ijcai.org/proceedings/2023/0734.pdf)  
8. Temporal Knowledge Graph Completion: A Survey \- IJCAI, accessed on June 17, 2025, [https://www.ijcai.org/proceedings/2023/734](https://www.ijcai.org/proceedings/2023/734)  
9. Temporal database \- Wikipedia, accessed on June 17, 2025, [https://en.wikipedia.org/wiki/Temporal\_database](https://en.wikipedia.org/wiki/Temporal_database)  
10. Bitemporal modeling \- Wikipedia, accessed on June 17, 2025, [https://en.wikipedia.org/wiki/Bitemporal\_modeling](https://en.wikipedia.org/wiki/Bitemporal_modeling)  
11. Position Paper: Bitemporal Dynamic Graph Analytics \- People, accessed on June 17, 2025, [https://people.ece.ubc.ca/matei/papers/grades2021.pdf](https://people.ece.ubc.ca/matei/papers/grades2021.pdf)  
12. Bitemporal Property Graphs to Organize Evolving ... \- Oracle APEX, accessed on June 17, 2025, [https://apexapps.oracle.com/pls/apex/f?p=LABS:0:109415517057944:APPLICATION\_PROCESS=GETDOC\_INLINE:::DOC\_ID:2442](https://apexapps.oracle.com/pls/apex/f?p=LABS:0:109415517057944:APPLICATION_PROCESS%3DGETDOC_INLINE:::DOC_ID:2442)  
13. A Glossary of Temporal Database Concepts \- SIGMOD Record, accessed on June 17, 2025, [https://sigmodrecord.org/publications/sigmodRecord/9209/pdfs/140979.140996.pdf](https://sigmodrecord.org/publications/sigmodRecord/9209/pdfs/140979.140996.pdf)  
14. Bitemporal Modeling \- Data Engineering Blog, accessed on June 17, 2025, [https://www.ssp.sh/brain/bitemporal-modeling/](https://www.ssp.sh/brain/bitemporal-modeling/)  
15. Beacon's Data Warehouse and Bi-Temporal Data Model, accessed on June 17, 2025, [https://www.beacon.io/wp-content/uploads/2022/04/5.-WhitePaper-Beacon-Data-Warehouse-and-Bi-Temporal-Data-Model.pdf](https://www.beacon.io/wp-content/uploads/2022/04/5.-WhitePaper-Beacon-Data-Warehouse-and-Bi-Temporal-Data-Model.pdf)  
16. Towards an event-centric knowledge graph approach for public administration, accessed on June 17, 2025, [https://ruomoplus.lib.uom.gr/bitstream/8000/1538/1/ECKG\_IEEE\_CBI\_2022.pdf](https://ruomoplus.lib.uom.gr/bitstream/8000/1538/1/ECKG_IEEE_CBI_2022.pdf)  
17. (PDF) Event-Centric Temporal Knowledge Graph Construction: A Survey \- ResearchGate, accessed on June 17, 2025, [https://www.researchgate.net/publication/376181551\_Event-Centric\_Temporal\_Knowledge\_Graph\_Construction\_A\_Survey](https://www.researchgate.net/publication/376181551_Event-Centric_Temporal_Knowledge_Graph_Construction_A_Survey)  
18. An Event-Centric Knowledge Graph Approach for Public ... \- MDPI, accessed on June 17, 2025, [https://www.mdpi.com/2073-431X/13/1/17](https://www.mdpi.com/2073-431X/13/1/17)  
19. Tutorial: AAAI-21: Event-Centric Natural Language Understanding \- Cognitive Computation Group, accessed on June 17, 2025, [https://cogcomp.seas.upenn.edu/page/tutorial.202102/](https://cogcomp.seas.upenn.edu/page/tutorial.202102/)  
20. Event Knowledge Graph: A Review Based on Scientometric Analysis \- MDPI, accessed on June 17, 2025, [https://www.mdpi.com/2076-3417/13/22/12338](https://www.mdpi.com/2076-3417/13/22/12338)  
21. Breaking Down the Data-Metadata Barrier for Effective Property Graph Data Management, accessed on June 17, 2025, [https://www.researchgate.net/publication/391766525\_Breaking\_Down\_the\_Data-Metadata\_Barrier\_for\_Effective\_Property\_Graph\_Data\_Management](https://www.researchgate.net/publication/391766525_Breaking_Down_the_Data-Metadata_Barrier_for_Effective_Property_Graph_Data_Management)  
22. Meta-Property Graphs: Extending Property Graphs with Metadata ..., accessed on June 17, 2025, [https://arxiv.org/pdf/2410.13813](https://arxiv.org/pdf/2410.13813)  
23. RDF vs. Property Graphs: Choosing the Right Approach for Implementing a Knowledge Graph \- Neo4j, accessed on June 17, 2025, [https://neo4j.com/blog/knowledge-graph/rdf-vs-property-graphs-knowledge-graphs/](https://neo4j.com/blog/knowledge-graph/rdf-vs-property-graphs-knowledge-graphs/)  
24. Graph Models, Structures and Knowledge Graphs, accessed on June 17, 2025, [https://graph.build/resources/graph-models](https://graph.build/resources/graph-models)  
25. data structures \- Adjustable, versioned graph database \- Stack Overflow, accessed on June 17, 2025, [https://stackoverflow.com/questions/28606507/adjustable-versioned-graph-database](https://stackoverflow.com/questions/28606507/adjustable-versioned-graph-database)  
26. Spatio-Temporal Foundation Models: Vision, Challenges, and Opportunities \- arXiv, accessed on June 17, 2025, [https://arxiv.org/html/2501.09045v1](https://arxiv.org/html/2501.09045v1)  
27. A Comprehensive Guide to Temporal Graphs in Data Science \- Analytics Vidhya, accessed on June 17, 2025, [https://www.analyticsvidhya.com/blog/2023/12/a-comprehensive-guide-to-temporal-graphs-in-data-science/](https://www.analyticsvidhya.com/blog/2023/12/a-comprehensive-guide-to-temporal-graphs-in-data-science/)  
28. Temporal and Spatial Analysis \- Graphaware, accessed on June 17, 2025, [https://graphaware.com/glossary/temporal-geospatial-analysis/](https://graphaware.com/glossary/temporal-geospatial-analysis/)  
29. Meta-Property Graphs: Extending Property Graphs with Metadata Awareness and Reification \- ResearchGate, accessed on June 17, 2025, [https://www.researchgate.net/publication/385010463\_Meta-Property\_Graphs\_Extending\_Property\_Graphs\_with\_Metadata\_Awareness\_and\_Reification](https://www.researchgate.net/publication/385010463_Meta-Property_Graphs_Extending_Property_Graphs_with_Metadata_Awareness_and_Reification)  
30. What Is RDF-star | Ontotext Fundamentals, accessed on June 17, 2025, [https://www.ontotext.com/knowledgehub/fundamentals/what-is-rdf-star/](https://www.ontotext.com/knowledgehub/fundamentals/what-is-rdf-star/)  
31. Edge properties, part 1: Reification \- Monkeying around with OWL, accessed on June 17, 2025, [https://douroucouli.wordpress.com/2020/09/11/edge-properties-part-1-reification/](https://douroucouli.wordpress.com/2020/09/11/edge-properties-part-1-reification/)  
32. Benchmarking the RDF and Property Graph Model in the Temporal ..., accessed on June 17, 2025, [https://dl.gi.de/bitstreams/b59966cc-0d98-45f4-8181-fedfd3393544/download](https://dl.gi.de/bitstreams/b59966cc-0d98-45f4-8181-fedfd3393544/download)  
33. Temporal Support | WaveMaker Docs, accessed on June 17, 2025, [https://www.wavemaker.com/learn/app-development/services/database-services/temporal-support/](https://www.wavemaker.com/learn/app-development/services/database-services/temporal-support/)  
34. T-Cypher – A temporal Graph Query Language, accessed on June 17, 2025, [https://project.inria.fr/tcypher/](https://project.inria.fr/tcypher/)  
35. Docs – T-Cypher, accessed on June 17, 2025, [https://project.inria.fr/tcypher/docs/](https://project.inria.fr/tcypher/docs/)  
36. Continuous Query Syntax \- Drasi Docs, accessed on June 17, 2025, [https://drasi.io/reference/query-language/](https://drasi.io/reference/query-language/)  
37. Event-Centric Temporal Knowledge Graph Construction: A Survey, accessed on June 17, 2025, [https://www.mdpi.com/2227-7390/11/23/4852](https://www.mdpi.com/2227-7390/11/23/4852)  
38. Transformer-Based Temporal Information Extraction and Application: A Review \- arXiv, accessed on June 17, 2025, [https://arxiv.org/html/2504.07470v1](https://arxiv.org/html/2504.07470v1)  
39. Named Entity Recognition (NER): Ultimate Guide | Encord, accessed on June 17, 2025, [https://encord.com/blog/named-entity-recognition/](https://encord.com/blog/named-entity-recognition/)  
40. Named Entity Recognition (with examples) \- Hex, accessed on June 17, 2025, [https://hex.tech/templates/sentiment-analysis/named-entity-recognition/](https://hex.tech/templates/sentiment-analysis/named-entity-recognition/)  
41. What Is Named Entity Recognition (NER): How It Works & More | Tonic.ai, accessed on June 17, 2025, [https://www.tonic.ai/guides/named-entity-recognition-models](https://www.tonic.ai/guides/named-entity-recognition-models)  
42. Temporal Reasoning in Natural Language Processing: A Survey \- International Journal of Computer Applications | IJCA, accessed on June 17, 2025, [https://www.ijcaonline.org/volume1/number4/pxc387209.pdf](https://www.ijcaonline.org/volume1/number4/pxc387209.pdf)  
43. A hybrid system for temporal information extraction from clinical text \- PMC, accessed on June 17, 2025, [https://pmc.ncbi.nlm.nih.gov/articles/PMC3756274/](https://pmc.ncbi.nlm.nih.gov/articles/PMC3756274/)  
44. Relation Extraction \- Papers With Code, accessed on June 17, 2025, [https://paperswithcode.com/task/relation-extraction](https://paperswithcode.com/task/relation-extraction)  
45. What is Event Extraction? \- NetOwl, accessed on June 17, 2025, [https://www.netowl.com/what-is-event-extraction](https://www.netowl.com/what-is-event-extraction)  
46. Named Entity Recognition (NER) in Python at Scale | John Snow Labs, accessed on June 17, 2025, [https://www.johnsnowlabs.com/named-entity-recognition-ner-with-python-at-scale/](https://www.johnsnowlabs.com/named-entity-recognition-ner-with-python-at-scale/)  
47. Relationship Extraction \- NLP-progress, accessed on June 17, 2025, [http://nlpprogress.com/english/relationship\_extraction.html](http://nlpprogress.com/english/relationship_extraction.html)  
48. UTG: Towards a Unified View of Snapshot and Event ... \- OpenReview, accessed on June 17, 2025, [https://openreview.net/pdf?id=ZKHV6Cpsxg](https://openreview.net/pdf?id=ZKHV6Cpsxg)  
49. \[2407.12269\] UTG: Towards a Unified View of Snapshot and Event Based Models for Temporal Graphs \- arXiv, accessed on June 17, 2025, [https://arxiv.org/abs/2407.12269](https://arxiv.org/abs/2407.12269)  
50. Snapshots in Event Sourcing \- Kurrent, accessed on June 17, 2025, [https://www.kurrent.io/blog/snapshots-in-event-sourcing](https://www.kurrent.io/blog/snapshots-in-event-sourcing)  
51. Auxo: A Temporal Graph Management System \- PACMAN Group, accessed on June 17, 2025, [https://pacman.cs.tsinghua.edu.cn/\~cwg/publication/auxo-2019/auxo-2019.pdf](https://pacman.cs.tsinghua.edu.cn/~cwg/publication/auxo-2019/auxo-2019.pdf)  
52. Aion: Efficient Temporal Graph Data Management \- OpenProceedings.org, accessed on June 17, 2025, [https://openproceedings.org/2024/conf/edbt/paper-124.pdf](https://openproceedings.org/2024/conf/edbt/paper-124.pdf)  
53. AeonG: An Efficient Built-in Temporal Support in Graph Databases \- VLDB Endowment, accessed on June 17, 2025, [https://www.vldb.org/pvldb/vol17/p1515-lu.pdf](https://www.vldb.org/pvldb/vol17/p1515-lu.pdf)  
54. Efficient Snapshot Retrieval over Historical Graph Data, accessed on June 17, 2025, [http://www.cs.albany.edu/\~jhh/courses/readings/khurana.icde13.snapshot.pdf](http://www.cs.albany.edu/~jhh/courses/readings/khurana.icde13.snapshot.pdf)  
55. Exploring Temporal and Spatial Graph Databases \- Hypermode, accessed on June 17, 2025, [https://hypermode.com/blog/spatial-vs-temporal](https://hypermode.com/blog/spatial-vs-temporal)  
56. The impact of indexes on query performance \- Cypher Manual \- Neo4j, accessed on June 17, 2025, [https://neo4j.com/docs/cypher-manual/current/indexes/search-performance-indexes/using-indexes/](https://neo4j.com/docs/cypher-manual/current/indexes/search-performance-indexes/using-indexes/)  
57. Indexing for Better Performance \- JanusGraph, accessed on June 17, 2025, [https://docs.janusgraph.org/v0.4/index-management/index-performance/](https://docs.janusgraph.org/v0.4/index-management/index-performance/)  
58. Indexing for Better Performance \- JanusGraph Docs, accessed on June 17, 2025, [https://docs.janusgraph.org/schema/index-management/index-performance/](https://docs.janusgraph.org/schema/index-management/index-performance/)  
59. Temporal Triangles: Real-World Graph Database Benchmark, accessed on June 17, 2025, [https://rocketgraph.com/2025/04/temporal-triangles-a-benchmark-for-the-modern-graph-era/](https://rocketgraph.com/2025/04/temporal-triangles-a-benchmark-for-the-modern-graph-era/)  
60. Scalable Time-Range k-Core Query on Temporal Graphs \- VLDB Endowment, accessed on June 17, 2025, [https://www.vldb.org/pvldb/vol16/p1168-zhong.pdf](https://www.vldb.org/pvldb/vol16/p1168-zhong.pdf)  
61. What is Query Optimization in Graph Databases? Techniques and Strategies \- Hypermode, accessed on June 17, 2025, [https://hypermode.com/blog/query-optimization](https://hypermode.com/blog/query-optimization)  
62. Query tuning \- Cypher Manual \- Neo4j, accessed on June 17, 2025, [https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/query-tuning/](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/query-tuning/)  
63. TGL: A General Framework for Temporal GNN Training on Billion-Scale Graphs \- VLDB Endowment, accessed on June 17, 2025, [https://www.vldb.org/pvldb/vol15/p1572-zhou.pdf](https://www.vldb.org/pvldb/vol15/p1572-zhou.pdf)  
64. ETC: Efficient Training of Temporal Graph Neural Networks over Large-scale Dynamic Graphs \- VLDB Endowment, accessed on June 17, 2025, [https://www.vldb.org/pvldb/vol17/p1060-gao.pdf](https://www.vldb.org/pvldb/vol17/p1060-gao.pdf)  
65. A temporal knowledge graph reasoning model based on recurrent encoding and contrastive learning \- PMC, accessed on June 17, 2025, [https://pmc.ncbi.nlm.nih.gov/articles/PMC11784877/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11784877/)