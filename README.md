# fuzzy-logic-search

**fuzzy-logic-search** is an academic and practical framework for querying structured and unstructured documents using fuzzy logic principles. Unlike traditional Boolean search techniques that yield a binary match or non-match, **fuzzy-logic-search** produces a continuous score in the range [0, 1], indicating the *degree-of-membership (DoM)*—or relevance—of each document to the given query.

This system supports queries on both structured JSON documents and flat text files, offering a uniform fuzzy logic interface to a variety of data sources. Users can compose queries using logical operators, quantifiers, modifiers, and custom predicates that return continuous or crisp DoM values, enabling rich, human-centric querying.

---

## Table of Contents

1. [Introduction](#introduction)  
2. [Core Concepts](#core-concepts)  
3. [Why Fuzzy Logic?](#why-fuzzy-logic)  
4. [Document Models and Identity](#document-models-and-identity)  
5. [Query Syntax and Semantics](#query-syntax-and-semantics)  
6. [Custom Predicates and Extensibility](#custom-predicates-and-extensibility)  
7. [Flat Document Support](#flat-document-support)  
8. [Homomorphism: Theory and Examples](#homomorphism-theory-and-examples)  
9. [Evaluation and Post-Processing](#evaluation-and-post-processing)  
10. [Examples](#examples)  
11. [Applications and Use Cases](#applications-and-use-cases)  
12. [Future Directions](#future-directions)  
13. [References](#references)

---

## Introduction

Conventional search often treats queries and documents as sharply delineated: a document either matches the query or it does not. Real-world reasoning, however, is often more nuanced. **fuzzy-logic-search** introduces gradation, allowing documents to match queries to varying extents. This can be crucial when dealing with heterogeneous datasets, ambiguous search terms, or user queries that are not strictly binary.

---

## Core Concepts

1. **Fuzzy Sets**:  
   A fuzzy set assigns to each element a membership value in [0, 1]. In **fuzzy-logic-search**, each document is assigned a degree of relevance to the query, reflecting partial matches rather than absolute inclusion or exclusion.

2. **Fuzzy Operations**:  
   Logical operators from Boolean logic (`and`, `or`, `not`) are extended using fuzzy logic. For instance:
   - `and` → *minimum* of the membership scores,
   - `or` → *maximum* of the membership scores,
   - `not` → *1 minus* the membership score.

3. **Linguistic Hedges (Modifiers)**:  
   Terms like `very` and `somewhat` transform membership values. For example:
   - `very Q` might square the DoM, emphasizing already-strong matches.
   - `somewhat Q` might take a square root, broadening tolerance to partial matches.

---

## Why Fuzzy Logic?

Fuzzy logic better models how humans interpret queries. Instead of forcing binary decisions, it allows for degrees of satisfaction. Benefits include:

- **Graduated Transitions**: Smoothly vary between full match and no match, rather than abrupt cutoffs.
- **Complex Queries**: Easily combine multiple conditions (e.g., `(and (field age (> 25)) (field name (contains "Smith")))`) and produce nuanced relevance scores.
- **Interpretability and Flexibility**: Fuzzy sets can be interpreted directly as numeric scores or, if desired, mapped back to linguistic categories (like "very relevant") through optional defuzzification.

---

## Document Models and Identity

**fuzzy-logic-search** supports two primary document types:

1. **Structured JSON Documents**:  
   Each JSON document may reside in its own file or be provided programmatically as a Python dictionary. Documents are identified by:
   - **Filename**: If loading from a file, the filename serves as the document’s ID.
   - **Hash**: If provided as a dictionary, a hash of the document is used as its ID.
   - **Index**: If documents are provided in a list with no other identifiers, their list index is used.

2. **Flat Documents (e.g., `.txt`, `.md`)**:  
   When fields are not applicable, documents are treated as raw text. Queries default to fuzzy logic operations on content-based similarity (e.g., normalized TF-IDF scores), providing a DoM that represents how well the document’s text aligns with the query terms.

---

## Query Syntax and Semantics

Queries are represented as abstract syntax trees (ASTs), enabling complex, composable logic. For example:

```lisp
(and 
  (field x (== 1)) 
  (not (field y (startswith z))))
```

This may parse to:

```json
[
  "and",
  ["field", "x", ["==", 1]],
  ["not", ["field", "y", ["startswith", "z"]]]
]
```

**Key Components**:
- **field path**: Specifies where in a JSON document to look.
- **predicates**: Such as `==`, `>`, `<`, `startswith`, or `contains`, yield a membership value.  
- **logical operators**: `and`, `or`, `not` apply fuzzy logic to combine or modify conditions.
- **modifiers**: `very`, `somewhat` and others can transform membership values.

---

## Custom Predicates and Extensibility

**fuzzy-logic-search** is fully extensible. Users can define their own predicates with custom membership logic. While default predicates often map to crisp Boolean tests (yielding 0.0 or 1.0), advanced users can integrate domain-specific scoring functions that return continuous values.

For example, you can define a custom predicate `_similar(ob, doc)` that returns a continuous similarity measure (e.g., cosine similarity, Jaccard index, or a learned embedding distance) normalized to [0,1].

Here is a snippet from the default predicate set (simplified):

```python
def _contains(ob, doc, quant=all) -> float:
    if isinstance(ob, list):
        return float(quant(str(o) in str(doc) for o in ob))
    else:
        return float(str(ob) in str(doc))
```

This returns 1.0 if `doc` contains `ob`, and 0.0 otherwise. Users can replace this logic or add new predicates that compute partial matches, graded similarities, or probabilistic scores.

---

## Flat Document Support

For flat documents without structured fields, **fuzzy-logic-search** defaults to similarity-based measures. For instance, when you query `(contains "Smith")` over a `.txt` file, an internal TF-IDF-based scoring mechanism might produce a relevance score proportional to the frequency and distinctiveness of `"Smith"` in the document. Thus, even plain text searches benefit from fuzzy logic, capturing how "strongly" a document matches rather than requiring an exact condition.

---

## Homomorphism: Theory and Examples

A notable mathematical property of this system is that the mapping from queries (`Q`) to result sets (`R`) is a **homomorphism**. This means:

1. Operations on queries translate directly to operations on their corresponding fuzzy result sets.
2. If you have queries `Q1` and `Q2`, and their corresponding result sets `R1` and `R2`, then:
   \[
   \Phi(Q1 \,\text{and}\, Q2) = \Phi(Q1) \,\text{and}\, \Phi(Q2) = R1 \cap R2
   \]
   where the `and` operation on results is applied element-wise to their membership values.

**Example**:  
- Suppose `Q1(d)` assigns a relevance of 0.8 to document `d`, and `Q2(d)` assigns 0.6.  
- `Q1 and Q2` would assign `min(0.8, 0.6) = 0.6` to `d`.  
- Likewise, the result sets `R1` and `R2` induced by `Q1` and `Q2` would yield a result `R = R1 and R2` that has the same minimal intersection membership.

This property ensures **consistency and predictability**: whether you combine fuzzy sets at the query level or at the result level, you arrive at the same final degrees of membership.

**Non-Invertibility**:  
While we can map `Q` to `R`, we cannot uniquely recover `Q` from `R`. Different queries may produce identical result sets, so the process is not invertible.

---

## Evaluation and Post-Processing

Evaluating a query `Q` over a document set `D` yields a fuzzy set `R`:
\[
R = \{(d, Q(d)) \mid d \in D \}
\]

Since both queries and results are fuzzy sets, you can post-process `R` using the same operations:
- Apply logical operators to combine multiple result sets (`R = R1 and (not R2)`).
- Use modifiers on results directly (`very R`), sharpening or broadening the final membership values without re-running the original queries.

This flexible architecture encourages iterative refinement, experimentation, and dynamic adjustment of search results after the initial computation.

---

## Examples

**Simple Structured Query**:
```lisp
(field age (> 25))
```
For a document `{"age": 30}`, this might yield a high membership (close to 1.0), while `{"age": 20}` might yield a lower membership (0.0 if crisp, or a partial score if using a graded comparison).

**Compound Query**:
```lisp
(and
  (field address.city (== "New York"))
  (not (field age (< 25))))
```
This increases membership for documents whose `address.city` closely matches `"New York"` and whose `age` is not less than 25, combining these conditions fuzzily.

**Post-Processing**:
If `R1` results from `Q1`, and `R2` from `Q2`, you can form a new result set:
```lisp
R = very (R1 or R2)
```
This applies the `or` (max) operation at the result level and then the `very` modifier to emphasize top matches.

---

## Applications and Use Cases

- **Search Engines**: Instead of returning a binary match, yield graded results that reflect partial matches and relevance strength.
- **Recommendation Systems**: Combine multiple user preference queries fuzzily, weighting attributes like price, popularity, and genre to produce a nuanced recommendation score.
- **Data Analysis**: Query large JSON datasets or plain text corpora with flexible, human-like reasoning, enabling exploratory data analysis and gradual refinement of search criteria.

---

## Future Directions

1. **Adaptive Defuzzification**: Map membership scores back to linguistic categories (e.g., "highly relevant", "mildly relevant") for user-facing explanations.
2. **Advanced Similarity Measures**: Integrate vector-based semantic similarity or machine learning–derived embeddings to produce more meaningful fuzzy matches.
3. **Performance and Indexing**: Scale to larger datasets with indexing and caching strategies, ensuring efficiency without compromising fuzzy logic principles.

---

## References

- Zadeh, L. A. (1965). *Fuzzy sets.* Information and Control, 8(3), 338–353.
- Klir, G. J., & Yuan, B. (1995). *Fuzzy sets and fuzzy logic: theory and applications.* Prentice Hall.
- Zimmermann, H.-J. (1996). *Fuzzy set theory—and its applications.* Springer.

---

**fuzzy-logic-search** offers a unified, theory-driven approach to querying documents—both structured and unstructured—through the lens of fuzzy logic. It encourages a more nuanced view of relevance, supports extensibility through custom predicates, and maintains a homomorphism between queries and their result sets. Ultimately, it stands as both a pedagogical tool and a practical system for modern information retrieval scenarios.