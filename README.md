
# Fuzzy Logic Search

A flexible and expressive system for querying structured JSON documents using
fuzzy logic principles. This system enables users to construct complex queries
that return fuzzy sets of results, capturing the degree of relevance of each
document to the query.

> We also support flat files. In this case, a compelling degree of relevance 
> score is something like a normalized `tf-idf` score on matching keywords in the
> query and the document. You could still use something like a levenshtein
> distance insetad, but it would likely not satisfy the information retrieval
> principles as well as `tf-idf` would.

---

## Features

- **Fuzzy Querying**: 
  - Construct queries using logical operators (`and`, `or`, `not`), modifiers (`very`, `somewhat`), and comparison predicates (`==`, `contains`, `startswith`, etc.).
  - Queries are expressed as structured abstract syntax trees (ASTs) for modularity and extensibility.
- **Structured Document Support**:
  - Operates on JSON documents stored as separate files in directories or provided as direct dictionary inputs.
- **Dual Fuzzy Representation**:
  - Queries are fuzzy sets, representing the degree of relevance of all documents.
  - Results are fuzzy sets, associating documents with degrees of membership (relevance).
- **Homomorphic Operations**:
  - Logical and modifier operations applied to queries propagate to result sets consistently.
- **Post-Processing Flexibility**:
  - Modify result sets dynamically with operations like `very`, `not`, or logical combinations.

---

## Document Identity System

### **1. File-Based Documents**
If documents are stored as separate JSON files, their **filename** serves as their unique identifier:
```json
{ "id": "funny.json", "relevance": 0.85 }
```

### **2. Hash-Based Identity**
If a JSON document is directly provided as a Python dictionary (e.g., via an API call), the system computes its **hash** to ensure a unique identity:
```json
{ "id": "abc123hash", "relevance": 0.85 }
```

### **3. Index-Based Identity**
In cases where documents are part of a list or batch with no explicit filenames or hashes, the **list index** serves as the identity:
```json
[ ..., 0.85, ... ]
```
- Example result: \( \{ "id": 5, "relevance": 0.85 \} \), where `id = 5` refers to the document’s position in the input list.

This flexible identity system ensures robust tracking of documents regardless of their source or storage format.

---

## Query Syntax

Queries are parsed into a list-based AST that is compatible with JSON for
evaluation. Here’s an example query:

### Example Query
```lisp
(and 
  (field x (== 1)) 
  (not (field y (startswith z))))
```

### Parsed as AST
```json
[
  "and",
  ["field", "x", ["==", 1]],
  ["not", ["field", "y", ["startswith", "z"]]]
]
```

The JSON representation of the query is more convenient for storage, serialization, and evaluation.
The representations are isomorphic, allowing easy conversion between the two
representations.

### Evaluation Process
1. Each `field` accesses a specified part of the JSON document.
2. Predicates like `==` or `startswith` evaluate fuzzy membership degrees for the field.
3. Logical operators (`and`, `or`, `not`) and modifiers (`very`, `somewhat`) combine and transform these degrees.

---

## Logical Framework

The system is grounded in fuzzy logic, providing consistent and interpretable results:

1. **Fuzzy Queries**:
   - Queries are fuzzy sets \( Q \), where \( Q(d) \in [0, 1] \) quantifies the degree to which a document \( d \) satisfies the query.

2. **Fuzzy Results**:
   - Applying \( Q \) to a document set \( D \) produces a result set \( R \), a fuzzy subset of \( D \):
     \[
     R = \{(d, Q(d)) \mid d \in D\}
     \]

3. **Logical Operators**:
   - Queries and results support fuzzy operations:
     - `and`: \(\min(Q_1(d), Q_2(d))\)
     - `or`: \(\max(Q_1(d), Q_2(d))\)
     - `not`: \(1 - Q(d)\)

4. **Modifiers**:
   - `very`: Sharpens membership degrees, e.g., \((Q(d))^2\).
   - `somewhat`: Broadens membership degrees, e.g., \(\sqrt{Q(d)}\).

5. **Homomorphism**:
   - Operations on queries propagate consistently to result sets:
     \[
     \Phi(Q_1 \text{ and } Q_2) = \Phi(Q_1) \cap \Phi(Q_2)
     \]

6. **Non-Invertibility**:
   - While \( Q \to R \) is well-defined, \( R \to Q \) is not generally possible due to the loss of query structure in \( R \).

---

## JSON Document Queries

This system supports querying nested and structured JSON documents with field-level specificity. Examples:

1. **Simple Field Query**
   ```lisp
   (field age (== 30))
   ```
   - Matches documents where the `age` field is approximately `30`.

2. **Wildcard Field Query**
   ```lisp
   (field person.*.name (contains "John"))
   ```
   - Matches documents where any nested `name` field under `person` contains "John".

3. **Compound Query**
   ```lisp
   (and
     (field address.city (== "New York"))
     (not (field age (< 25))))
   ```
   - Matches documents where the `address.city` field equals "New York" and `age` is not less than 25.

---

## Result Post-Processing

Result sets are fuzzy sets of documents. Post-processing allows dynamic adjustments:

- **Combine Results**:
  - Combine result sets logically: 
    ```lisp
    R = R1 and R2 or not R3
    ```

- **Apply Modifiers**:
  - Transform results dynamically:
    ```lisp
    R = very R1
    ```

This flexibility makes the system ideal for dynamic query refinement and iterative exploration.

---

## Example Workflow

### Query
```lisp
(and
  (field age (> 25))
  (field name (contains "Smith")))
```

### JSON Document
```json
{
  "age": 30,
  "name": "John Smith"
}
```

### Result
```json
{
  "id": "funny.json",
  "relevance": 0.85
}
```

---

## Applications

1. **Search Engines**:
   - Query structured data with fine-grained control and relevance ranking.
2. **Recommendation Systems**:
   - Combine fuzzy logic with user-defined preferences for personalized results.
3. **Data Analysis**:
   - Extract insights from JSON datasets with flexible, composable queries.

---

## Advantages

- **Expressive Queries**:
  - Support for modifiers, wildcards, and hierarchical fields.
- **Flexible Identity System**:
  - Supports filenames, hashes, or list indices to uniquely identify documents.
- **Dynamic Refinement**:
  - Post-process results without re-evaluating queries.

---

This system is a robust application of fuzzy logic principles to structured data querying, ensuring flexibility and consistency across diverse data formats and use cases.