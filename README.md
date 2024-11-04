# Boolean and Fuzzy Boolean Query Framework

A flexible Python framework for constructing, combining, and evaluating Boolean and Fuzzy Boolean queries against a collection of documents. This framework supports both strict binary evaluations and degrees-of-membership evaluations, laying the groundwork for advanced fuzzy set-theoretic query capabilities.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Boolean Queries](#boolean-queries)
  - [Fuzzy Boolean Queries](#fuzzy-boolean-queries)
- [API Documentation](#api-documentation)
  - [BooleanQuery](#booleanquery)
  - [FuzzyBooleanQuery](#fuzzybooleanquery)
  - [ResultQuery](#resultquery)
- [Formal Theory](#formal-theory)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Boolean Query Construction**: Create complex Boolean queries using `AND`, `OR`, and `NOT` operations.
- **Fuzzy Boolean Query Construction**: Extend Boolean queries with fuzzy logic operations and modifiers like `very` and `somewhat`.
- **Operator Overloading**: Combine queries intuitively using Python's bitwise operators (`&`, `|`, `~`).
- **Unified Evaluation Results**: Utilize a single `ResultQuery` class to handle both Boolean and Fuzzy Boolean query evaluations.
- **TF-IDF Integration**: Utilize Term Frequency-Inverse Document Frequency (TF-IDF) for sophisticated scoring in fuzzy queries.
- **Extensible Design**: Easily extend the framework with additional modifiers or integrate more complex scoring mechanisms.

## Installation

Ensure you have Python 3.7 or higher installed.

Clone the repository:

```bash
git clone https://github.com/queelius/algebraic_search.git
cd algebraic_search
```

## Usage

### Boolean Queries

Create and evaluate strict Boolean queries to determine document matches based on term presence.

```python
from boolean_query import BooleanQuery, ResultQuery

# Initialize BooleanQuery instances
q1 = BooleanQuery("cat dog") # same as BooleanQuery("(and cat dog)")
q2 = BooleanQuery("(or fish bird)")
q3 = ~q2
q4 = q1 & q3  # Represents "(and (and cat dog) (not (or fish bird)))"

# Example documents as sets
documents = [
    {"cat", "dog"},
    {"fish"},
    {"bird"},
    {"cat", "dog", "fish"},
    {"cat", "dog", "bird"},
    {"cat"},
    {"dog"},
    {"fish", "bird"},
    {"cat", "dog", "fish", "bird"},
]

# Evaluate queries against documents
results = q4.eval(documents)
print(q4)
# Output: (and (and cat dog) (not (or fish bird)))
print(results)
# Output: ResultQuery([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
```

### Fuzzy Boolean Queries

Construct and evaluate fuzzy Boolean queries that consider degrees of term relevance using TF-IDF scores.

```python
from fuzzy_boolean_query import FuzzyBooleanQuery, ResultQuery

# Sample documents
documents_text = [
    "cat dog",
    "fish",
    "bird",
    "cat dog fish",
    "cat dog bird",
    "cat",
    "dog",
    "fish bird",
    "cat dog fish bird",
]

# Compute TF-IDF scores
tfidf_scores, vocabulary = FuzzyBooleanQuery.compute_tfidf(documents_text)

# Initialize FuzzyBooleanQuery with TF-IDF data
q1_fuzzy = FuzzyBooleanQuery("cat dog", tfidf_matrix=tfidf_scores, vocabulary=vocabulary)
q2_fuzzy = FuzzyBooleanQuery("(or fish bird)", tfidf_matrix=tfidf_scores, vocabulary=vocabulary)
q3_fuzzy = ~q2_fuzzy
q4_fuzzy = q1_fuzzy & q3_fuzzy  # Represents "(and (and cat dog) (not (or fish bird)))"

# Evaluate queries against documents
results = q4_fuzzy.eval(documents_text)
print(q4_fuzzy) # Output: (and (and cat dog) (not (or fish bird)))
print(results)  # Output: ResultQuery([...]) with float scores
```

## API Documentation

### BooleanQuery

A class for constructing and evaluating strict Boolean queries.

#### Initialization

```python
BooleanQuery(query: Union[str, List] = None)
```

- `query`: A query string (e.g., `"cat dog"`, `"(or fish bird)"`) or a list of tokens. Defaults to an empty query.

#### Methods

- `tokenize(query: str) -> List`: Parses the query string into a nested list structure.
- `eval(docs: Union[List[Set[str]], Set[str]]) -> ResultQuery`: Evaluates the query against a list of documents.
- Operator Overloads:
  - `&`: Logical AND
  - `|`: Logical OR
  - `~`: Logical NOT

#### Example

```python
q = BooleanQuery("(and cat dog)")
result = q.eval([{"cat", "dog"}, {"cat"}, {"dog"}, {"cat", "dog"}])
print(result)  # ResultQuery([1.0, 0.0, 0.0, 1.0])
```

### FuzzyBooleanQuery

A class for constructing and evaluating fuzzy Boolean queries with degrees of membership.

#### Initialization

```python
FuzzyBooleanQuery(query: Union[str, List])
```

- `query`: A query string or list of tokens.

#### Methods

- `tokenize(query: str) -> List`: Parses the query string into a nested list structure, recognizing fuzzy modifiers.
- `eval(docs: List[str], ranker: Callable) -> ResultQuery`: Evaluates the fuzzy query against a list of documents using some ranker, like a normalized TF-IDF score.
- Operator Overloads:
  - `&`: Logical AND (fuzzy)
  - `|`: Logical OR (fuzzy)
  - `~`: Logical NOT (fuzzy)

#### Example

```python
q_fuzzy = FuzzyBooleanQuery("cat dog")
result_fuzzy = q_fuzzy.eval(docs, ranker=lambda term, doc: 1.0 if term in doc else 0.0)
print(result_fuzzy)  # ResultQuery([...])
```

### ResultQuery

Represents the results of evaluating both `BooleanQuery` and `FuzzyBooleanQuery`.

#### Attributes

- `scores`: A list of floats (`0.0` or `1.0` for Boolean queries, `0.0` to `1.0` for Fuzzy Boolean queries) indicating the degree of membership for each document.

#### Methods

- Operator Overloads:
  - `&`: Element-wise minimum
  - `|`: Element-wise maximum
  - `~`: Element-wise complement

#### Example

```python
r1 = ResultQuery([1.0, 0.0, 1.0])
r2 = ResultQuery([0.5, 1.0, 0.0])  # For BooleanQuery, these should be 0.0 or 1.0
combined = r1 & r2  # ResultQuery([0.5, 0.0, 0.0])
```

*Note*: In `BooleanQuery`, scores should be strictly `0.0` or `1.0`. For `FuzzyBooleanQuery`, scores range between `0.0` and `1.0`.

## Formal Theory

### Boolean Algebra for Queries and Results

#### Query Algebra (`Q`)

- **Elements**: `Q = P(T*)` where `T*` is the set of all finite strings composed of ASCII characters. `P(T*)` is the power set of `T*`.
- **Operations**:
  - **AND (`&`)**: Intersection of two subsets.
  - **OR (`|`)**: Union of two subsets.
  - **NOT (`~`)**: Complement of a subset relative to `T*`.
- **Constants**:
  - **Empty Set (`{}`)**: Matches no documents.
  - **Universal Set (`T*`)**: Matches all documents.

#### Result Algebra (`R`)

- **Elements**: `R = [r_1, r_2, ..., r_n]` where each `r_i` ∈ {0.0, 1.0} for Boolean queries or `r_i` ∈ [0.0, 1.0] for Fuzzy Boolean queries.
- **Operations**:
  - **AND (`&`)**: Element-wise minimum.
  - **OR (`|`)**: Element-wise maximum.
  - **NOT (`~`)**: Element-wise complement (`1.0 - r_i`).

#### Homomorphism

The evaluation functions `BooleanQuery.eval` and `FuzzyBooleanQuery.eval` serve as homomorphisms `φ: Q → R` and `φ_f: Q_f → R_f`, preserving the algebraic structure:

- `φ(Q1 & Q2) = φ(Q1) & φ(Q2)`
- `φ(Q1 | Q2) = φ(Q1) | φ(Q2)`
- `φ(~Q1) = ~φ(Q1)`
- Similarly for fuzzy queries.

### Fuzzy Boolean Algebra for Queries and Results

#### Fuzzy Query Algebra (`Q_f`)

- **Elements**: `Q_f = P(T*)` similar to Boolean queries.
- **Operations**:
  - **AND (`&`)**: Fuzzy intersection using minimum.
  - **OR (`|`)**: Fuzzy union using maximum.
  - **NOT (`~`)**: Fuzzy complement (`1.0 - x`).
  - **Modifiers**: Such as `very`, `somewhat`, etc., to adjust degrees of membership.

#### Fuzzy Result Algebra (`R_f`)

- **Elements**: `R_f = [r_1, r_2, ..., r_n]` where each `r_i` ∈ [0.0, 1.0].
- **Operations**:
  - **AND (`&`)**: Element-wise minimum.
  - **OR (`|`)**: Element-wise maximum.
  - **NOT (`~`)**: Element-wise complement (`1.0 - r_i`).

#### Homomorphism

The evaluation function `eval` in both `BooleanQuery` and `FuzzyBooleanQuery` acts as a homomorphism `φ: Q → R` and `φ_f: Q_f → R_f`, preserving:

- **Preservation of Operations**:
  - `φ(Q1 & Q2) = φ(Q1) & φ(Q2)`
  - `φ(Q1 | Q2) = φ(Q1) | φ(Q2)`
  - `φ(~Q1) = ~φ(Q1)`
- **Preservation of Modifiers**:
  - `φ_f(very Q) = very φ_f(Q)`
  - `φ_f(somewhat Q) = somewhat φ_f(Q)`

This ensures that the logical and fuzzy structures of queries are faithfully represented in the evaluation results.

## Future Enhancements

- **Advanced Fuzzy Operators**: Incorporate more sophisticated fuzzy logic operators and modifiers.
- **Custom Scoring Mechanisms**: Implement alternative scoring strategies beyond TF-IDF, such as BM25.
- **Caching and Optimization**: Optimize performance for large document collections through caching and efficient data structures.
- **Extended Query Language**: Support more complex query constructs and natural language processing features.
- **Integration with Databases and Search Engines**: Facilitate seamless integration with existing data storage and retrieval systems.

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the Repository**: Click the "Fork" button on the repository page.
2. **Clone Your Fork**:
   ```bash
   git clone https://github.com/queelius/algebraic_search.git
   cd algebraic_search
   ```
3. **Create a New Branch**:
   ```bash
   git checkout -b feature/YourFeatureName
   ```
4. **Make Your Changes**: Implement your feature or bug fix.
5. **Commit Your Changes**:
   ```bash
   git commit -m "Add your detailed commit message"
   ```
6. **Push to Your Fork**:
   ```bash
   git push origin feature/YourFeatureName
   ```
7. **Create a Pull Request**: Navigate to the original repository and click "Compare & pull request."

Please ensure that your code adheres to the existing style and includes relevant tests.

## License

This project is licensed under the [MIT License](LICENSE).

