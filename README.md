# fuzzy-logic-search (`fls`)

`fls` is an academic and practical framework for querying structured documents (JSON objects) using fuzzy logic principles. Unlike traditional Boolean search techniques that yield a binary relevant or non-relevant class label, `fls` produces a score in the range `[0, 1]`, indicating the *degree-of-membership* (DoM) that each document has with respect to a given query. The query itself defines a fuzzy set, and the documents are evaluated based on their overlap with this set.

This system supports queries on structured JSON documents, offering a uniform fuzzy logic interface to a variety of data sources. Users can compose queries using logical operators, quantifiers, modifiers, and custom predicates that return continuous or crisp DoM values, enabling rich, human-centric querying.

> NOTE: If you have flat text documents (e.g., `.txt`, `.md`), `fls` can still process them by treating them as a a single JSON `value` of type `string`, although the power of the `path` (to be discussed later) will not be available to define more complex fuzzy queries.

## Table of Contents

- [fuzzy-logic-search (`fls`)](#fuzzy-logic-search-fls)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Core Concepts](#core-concepts)
  - [Why Fuzzy Logic?](#why-fuzzy-logic)
  - [Document Models and Identity](#document-models-and-identity)
  - [Query Syntax and Semantics](#query-syntax-and-semantics)
  - [Relevance Scoring](#relevance-scoring)
  - [Default Fuzzy Predicates](#default-fuzzy-predicates)
    - [Default Fuzzy Membership Functions](#default-fuzzy-membership-functions)
      - [Triangular Membership Function for Numeric Equality](#triangular-membership-function-for-numeric-equality)
      - [Triangular Membership Function for Numeric Inequality](#triangular-membership-function-for-numeric-inequality)
      - [Levenshtein Distance-Based Membership Function for String Equality (( s\_1 = s\_2 ))](#levenshtein-distance-based-membership-function-for-string-equality--s_1--s_2-)
    - [Customization and Extensibility](#customization-and-extensibility)
    - [Supported Fuzzy Predicates](#supported-fuzzy-predicates)
    - [Sub-Queries and JSON Path Integration](#sub-queries-and-json-path-integration)
  - [Homomorphism: Theory and Examples](#homomorphism-theory-and-examples)
  - [Evaluation and Post-Processing](#evaluation-and-post-processing)
  - [Examples](#examples)
  - [Applications and Use Cases](#applications-and-use-cases)
  - [Future Directions](#future-directions)
  - [Conclusion](#conclusion)
  - [References](#references)

## Introduction

Conventional search often treats queries and documents as sharply delineated: a document either matches the query or it does not. Real-world reasoning, however, is often more nuanced. `fls` introduces gradation, allowing documents to match queries to varying extents. This can be salient when dealing with heterogeneous datasets (a collection of JSON documents with a non-uniform structure), ambiguous search terms, or information needs that are not easily captured by crisp logic.

## Core Concepts

- **Fuzzy Sets**:  
   A fuzzy set assigns to each element a membership value in [0, 1]. In `fls`, each document is assigned a degree of relevance to the query, reflecting partial matches rather than absolute inclusion or exclusion.

- **Fuzzy Operations**:  
   Logical operators from Boolean logic (`and`, `or`, `not`) are extended using fuzzy logic. For instance:
  - `and` → *minimum* of the membership scores,
  - `or` → *maximum* of the membership scores,
  - `not` → *1 minus* the membership score.

- **Linguistic Hedges (Modifiers)**:  
   Terms like `very` and `somewhat` transform membership values. For example:
  - `very Q` might square the DoM, emphasizing already-strong matches.
  - `somewhat Q` might take a square root, broadening tolerance to partial matches.

## Why Fuzzy Logic?

Fuzzy logic better models how humans interpret queries. Instead of forcing binary decisions, it allows for degrees of satisfaction. Benefits include:

- **Graduated Transitions**: Smoothly vary between full match and no match, rather than abrupt cutoffs.
- **Complex Queries**: Easily combine multiple conditions (e.g., `(or (> :age 25) (in? "smith" (lower-case :name))`) and produce nuanced relevance scores.
- **Interpretability and Flexibility**: Fuzzy sets can be interpreted directly as numeric scores or, if desired, mapped back to linguistic categories (like "very relevant") through optional defuzzification.

## Document Models and Identity

In `fls`, documents are represented as structured JSON objects. This choice offers a flexible and intuitive way to model complex data, enabling rich queries that leverage the hierarchical nature of JSON. Each JSON document may reside in its own file or be provided programmatically as a Python dictionary. Documents are identified by:

- **Filename**: If loading from a file, the filename serves as the document's ID.
- **Key**: If a dictionary is provided, the key is used as the document ID.
- **Index**: If an array of documents is provided, the index is used as the document ID. This also works when loading a list of files (e.g., the sorted list of filenames in a directory).
- **Hash**: Each document may also be identified by its hash, although duplicate documents that only differ by filename or key will be treated as identical.
- **Custom ID**: Users can specify a custom ID function of type `(JSON, **kwargs) -> string`, where `**kwargs` are additional arguments passed to the ID functionm, like the filename or key.

This flexible identity system allows for seamless integration with various data sources, enabling users to query documents based on their unique identifiers.

## Query Syntax and Semantics

Queries are represented as abstract syntax trees (ASTs), enabling complex, composable logic. For example:

```lisp
(very (and 
  (somewhat (== (:asset.amount) 1) )
  (very (not (starts-with? :name z)))))
```

This may parse to:

```json
[ "very", 
   [
      "and",
         ["somewhat", ["==", ["path", "asset.amount"], 1]],
         ["very", ["not", ["starts-with?", ["path", "name"], "z"]]]
   ]
]
```

**Key Components**:

- **field path**: Specifies where in a JSON document to look.
- **predicates**: Such as `==`, `>`, `<`, `starts-with?`, or `in?` yield a membership value.  
- **logical operators**: `and`, `or`, `not` apply fuzzy logic to combine or modify membership values based on membership
   values of subqueries. We may also view `and` and `or` as quantifiers, akin to "for all" and "there exists" (or any).
- **modifiers**: `very`, `somewhat` and other modifiers map membership values to new membership values (within [0, 1]).
- **general functions**: `lower-case`, `length`, `word-count`, `sum`, `mean`, `max`, `min`, `concat`, `unique`, `sort`, and more can be used to transform values before applying predicates.

> Note: The inclusion of general functions also allows for non-fuzzy operations, such as filtering, mapping, and reducing lists. This is also a valid use case for `fls`, but it is not the primary focus of the package as it does not return a fuzzy set, but a list of values corresponding to each document.

## Relevance Scoring

For JSON string values, there are a host of functions that may be used to score
relevance. These include (but are not limited to, and each is normalized to [0, 1]):

- `tf-idf`: the term frequency-inverse document frequency score, which is a measure of how important a word is to a document in a collection or corpus.
- `jaccard`: the Jaccard similarity between two strings.
- `levenshtein`: the Levenshtein distance between two strings.
- `cosine-sim`: the cosine similarity between embeddings of two strings.
- `word2vec`: This function does not compute a score, but rather returns the `word2vec` embedding of a string. Subsequent functions can be used to compute a score, like cosine similarity.

## Default Fuzzy Predicates

In our `fls` package, we offer a comprehensive framework for performing fuzzy searches on structured JSON documents. The package includes default fuzzy membership functions for common numeric comparisons and string comparisons, which can be easily customized or overridden to fit specific requirements. Additionally, a wide array of fuzzy predicates enables versatile and nuanced querying capabilities.

### Default Fuzzy Membership Functions

In what follows, we showcase three default fuzzy membership functions that underpin the fuzzy predicates in our package. These functions are designed to provide smooth and intuitive relevance scores based on the degree of match between query conditions and document fields.

#### Triangular Membership Function for Numeric Equality

This function evaluates the degree of equality between two numeric values $x$ and $y$,

$$
\mu_{\text{equal}}(x, y) =
\begin{cases}
1 - \dfrac{|x - y|}{\epsilon} & \text{if } |x - y| \leq \epsilon, \\
0 & \text{otherwise},
\end{cases}
$$

where the adaptive tolerance
$$
\epsilon = k \cdot \max\left(|x|,\, |y|,\, \delta\right)
$$
scales with the input values to provide a smooth transition from full membership to no membership and $k$ is a small constant (e.g., 0.01) that determines the relative tolerance.

#### Triangular Membership Function for Numeric Inequality

This function assesses the degree to which $x$ is less than or equal to $y$,

$$
\mu_{\leq}(x, y) =
\begin{cases}
1 & \text{if } x \leq y - \epsilon, \\
1 - \dfrac{x - (y - \epsilon)}{2\epsilon} & \text{if } y - \epsilon < x \leq y + \epsilon, \\
0 & \text{if } x > y + \epsilon,
\end{cases}
$$

where the adaptive tolerance
$$
\epsilon = k \cdot \max\left(|x|,\, |y|,\, \delta\right)
$$
scales with the input values to provide a smooth transition from full membership to no membership and $k$ is a small constant (e.g., 0.01) that determines the relative tolerance.

#### Levenshtein Distance-Based Membership Function for String Equality

This function computes the Levenshtein distance between two strings \( s_1 \) and \( s_2 \) and maps it to a relevance score based on a predefined threshold \( \tau \). The relevance score decreases linearly with the Levenshtein distance, ensuring a smooth transition from full membership to no membership. Here is how the membership function is defined:

$$
\mu_{\mathrm{str\_equal}}(s_1, s_2) = 1 - \frac{\mathrm{lev}(s_1, s_2)}{\tau}.
$$

*Parameters*:

- $\tau$: A threshold value determining the maximum Levenshtein distance for full membership. Defaults to $\tau = \max(|s_1|, |s_2|)$ where $|s|$ denotes the length of string $s$.

Levenshtein distance $\mathrm{lev}(s_1, s_2)$ computes the single-character edits required to transform string $s_1$ into string $s_2$. We normalize this distance by the threshold $\tau$ to obtain a relevance score in the range $[0, 1]$.


### Customization and Extensibility

While we provide robust defaults for fuzzy predicates like equality and inequality, our package is designed with flexibility in mind. Users can override these defaults to tailor the fuzzy logic behavior to their specific needs.

### Supported Fuzzy Predicates

Our package supports a diverse set of **fuzzy predicates** that can be applied to JSON values, enabling a wide range of query types. Some of the supported fuzzy predicates include:

- `==` (also `eq?`): Fuzzy equality
- `>` (also `lt?`): Greater than
- `<` (also `gt?`): Less than
- `>=` (also `gte?`): Greater than or equal to
- `<=` (also `lte?`): Less than or equal to
- `in?`: Membership within a range or set
- `starts-with?`: String prefix matching
- `ends-with?`: String suffix matching
- `contains?`: Substring matching
- `regex?`: Regular expression matching, this defaults to a crisp match
- `word2vec?`: Cosine similarity between strings based on their word embeddings
- `jaccard?`: Jaccard similarity between lists
- `tf-idf?`: Normalized TF-IDF score between the query string and the JSON value
- `lev?`: Normalized levenshtein distance between strings
- ...and many more

For a complete list of available fuzzy predicates and their implementations, please refer to the [GitHub repository](https://github.com/queelius/fls).

### Sub-Queries and JSON Path Integration

In addition to fuzzy predicates, our package facilitates **sub-queries** that extract values from specific JSON paths within your documents. These sub-queries do not directly receive degrees-of-membership. Instead, fuzzy predicates are applied to the output of these sub-queries, at which point the corresponding membership functions assign a relevance score based on the fuzzy logic rules.

**Example Workflow:**

- **Sub-Query**: Extract a value from a JSON path (e.g., `user.age`).
- **Predicate Application**: Apply a fuzzy predicate (e.g., `>=`) to the extracted value.
- **Scoring**: The predicate evaluates the condition and assigns a DoM, influencing the overall relevance score of the document.

This workflow allows for fine-grained control over the relevance scoring process, enabling complex queries that leverage both JSON structure and fuzzy logic predicates.

Here is a sample of functions that can be used to map JSON values to other values:

- `path`: Extracts a value from a JSON path, based on dot-separated keys and array indices. Wildcards `*` and `**` are supported, along with array slicing.
- `lower-case`: Converts a string to lowercase.
- `length`: Computes the length of a string or list.
- `word-count`: Counts the number of words in a string.
- `sum`: Computes the sum of a list of numbers.
- `mean`: Computes the mean of a list of numbers.
- `max`: Computes the maximum value in a list.
- `min`: Computes the minimum value in a list.
- `concat`: Concatenates a list of strings.
- `unique`: Returns unique elements in a list.
- `sort`: Sorts a list of numbers or strings.
- `reverse`: Reverses a list of numbers or strings.
- `flatten`: Flattens a nested list.
- `slice`: Extracts a sub-list based on start and end indices.
- `filter`: Filters a list based on a predicate function.
- `map`: Applies a function to each element of a list.
- `reduce`: Reduces a list to a single value using a binary function.
- ...and many more.

## The `path` Function

The `path` function is a key component of the `fls` package, allowing users to extract values from JSON documents based on specific paths. This function is particularly useful for querying structured data and applying fuzzy predicates to the extracted values. The `path` function supports a variety of features, including:

- **Dot-separated keys**: Traverse nested JSON objects using dot-separated keys (e.g., `user.name`).
- **Array indices**: Access elements in JSON arrays using zero-based indices (e.g., `users.[3].name`).
- **Wildcards**: Use `*` to match any key or index at a given level (e.g., `users.*.name`).
- **Recursive wildcards**: Use `**` to match any key or index at any level of nesting (e.g., `users.**.name`).

The `path` function provides a powerful mechanism for extracting values from JSON documents, enabling users to build complex queries that leverage the hierarchical structure of the data.

## Homomorphism: Theory and Examples

A notable mathematical property of this system is that the mapping from queries (`Q`) to result sets (`R`) is a **homomorphism**. This means:

1. Operations on queries translate directly to operations on their corresponding fuzzy result sets.
2. If you have queries `Q1` and `Q2`, and their corresponding result sets `R1` and `R2`, then:
   $$
   \Phi(Q1 \mathrm{and}\, Q2) = \Phi(Q1) \mathrm{and}\, \Phi(Q2) = R1 \cap R2
   $$
   where the `and` operation on results is applied element-wise to their membership values.

**Example**:

- Suppose `Q1(d)` assigns a relevance of 0.8 to document `d`, and `Q2(d)` assigns 0.6.  
- `Q1 and Q2` would assign `min(0.8, 0.6) = 0.6` to `d`.  
- Likewise, the result sets `R1` and `R2` induced by `Q1` and `Q2` would yield a result `R = R1 and R2` that has the same minimal intersection membership.

This property ensures **consistency and predictability**: whether you combine fuzzy sets at the query level or at the result level, you arrive at the same final degrees of membership.

**Non-Invertibility**:  
While we can map `Q` to `R`, we cannot uniquely recover `Q` from `R`. Different queries may produce identical result sets, so the process is not invertible.

## Evaluation and Post-Processing

Evaluating a query `Q` over a document set `D` yields a fuzzy set `R`:
$$
R = \{(d, Q(d)) \mid d \in D \}
$$

Since both queries and results are fuzzy sets, you can post-process result `R` using the same fuzzy operations:

- Apply logical operators to combine multiple result sets (`R = R1 and (not R2)`).
- Use modifiers on results directly (`very(R)`), sharpening or broadening the final membership values without re-running the original queries.

This flexible architecture encourages iterative refinement, experimentation, and dynamic adjustment of search results after the initial computation.

## Examples

**Simple Structured Query**:

```lisp
(> :age 25)
```

For a document `{"age": 30}`, this might yield a high membership (close to 1.0), while `{"age": 20}` might yield a lower membership (0.0 if crisp, or a partial score if using a graded comparison).

**Compound Query**:

```lisp
(and
  (== :address.city "New York")
  (not (< :age 25)))
```

This increases membership for documents whose `address.city` closely matches `"New York"` and whose `age` is not less than 25, combining these conditions fuzzily.

**Post-Processing**:
If `R1` results from `Q1`, and `R2` from `Q2`, you can form a new result set:

```lisp
R = very (R1 or R2)
```

This applies the `or` (max) operation at the result level and then the `very` modifier to emphasize top matches.

## Applications and Use Cases

- **Search Engines**: Instead of returning a binary match, yield graded results that reflect partial matches and relevance strength.
- **Recommendation Systems**: Combine multiple user preference queries fuzzily, weighting attributes like price, popularity, and genre to produce a nuanced recommendation score.
- **Data Analysis**: Query large JSON datasets or plain text corpora with flexible, human-like reasoning, enabling exploratory data analysis and gradual refinement of search criteria.

## Future Directions

- **Defuzzification**: Map membership scores back to linguistic categories (e.g., "highly relevant", "mildly relevant") for user-facing explanations.
- **Performance and Indexing**: Scale to larger datasets with indexing and caching strategies, ensuring efficiency without compromising fuzzy logic principles.

## Conclusion

`fls` offers a unified, theory-driven approach to querying JSON documents through the lens of fuzzy logic. It encourages a more nuanced view of relevance, supports extensibility through custom fuzzy predicates, and maintains a homomorphism between queries and their result sets. Ultimately, it stands as both a pedagogical tool and a practical system for modern information retrieval scenarios.

## References

- Zadeh, L. A. (1965). *Fuzzy sets.* Information and Control, 8(3), 338–353.
- Klir, G. J., & Yuan, B. (1995). *Fuzzy sets and fuzzy logic: theory and applications.* Prentice Hall.
- Zimmermann, H.-J. (1996). *Fuzzy set theory—and its applications.* Springer.
