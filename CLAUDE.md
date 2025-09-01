# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`fuzzy-logic-search` (fls) is an academic and practical framework for querying structured JSON documents using fuzzy logic principles. Unlike traditional Boolean search (like the jaf repository), fls produces continuous relevance scores in [0,1] representing degrees-of-membership, enabling nuanced, human-centric querying with gradual transitions between matches.

## Core Architecture

### Main Components

- **`fuzzy-logic-search/fuzzy_set.py`**: Core FuzzySet class representing fuzzy collections with membership degrees
- **`fuzzy-logic-search/fuzzy_query.py`**: FuzzyQuery class for constructing and evaluating fuzzy logic queries
- **`fuzzy-logic-search/fuzzy_json_query.py`**: JSON document querying with fuzzy logic evaluation
- **`fuzzy-logic-search/fuzzy_set_algebra.py`**: Fuzzy set operations (union, intersection, complement)
- **`fuzzy-logic-search/fuzzy_set_mods.py`**: Fuzzy modifiers (very, somewhat, slightly, extremely)
- **`fuzzy-logic-search/defuzz_fuzzy_set.py`**: Defuzzification methods for converting fuzzy sets to crisp values
- **`fuzzy-logic-search/default_preds.py`**: Default fuzzy predicates and membership functions
- **`fuzzy-logic-search/fuzzy_set_sampling.py`**: Sampling methods for fuzzy sets
- **`fuzzy-logic-search/utils/`**: Utility modules for corpus handling, stemming, etc.

### Query System

Queries use S-expression/Lisp-like syntax or JSON arrays:
```lisp
(very (and 
  (somewhat (== (:asset.amount) 1))
  (very (not (starts-with? :name z)))))
```

Equivalent JSON AST:
```json
["very", 
  ["and",
    ["somewhat", ["==", ["path", "asset.amount"], 1]],
    ["very", ["not", ["starts-with?", ["path", "name"], "z"]]]
  ]
]
```

### Fuzzy Operations & Modifiers

**Logical Operations** (fuzzy extensions):
- `and`: minimum of membership scores
- `or`: maximum of membership scores  
- `not`: 1 minus membership score

**Fuzzy Modifiers**:
- `very`: squares membership (emphasizes strong matches)
- `somewhat`: square root of membership (broadens tolerance)
- `slightly`: 10th root of membership
- `extremely`: cubes membership

**Fuzzy Predicates**:
- Numeric: `==`, `>`, `<`, `>=`, `<=` with triangular membership functions
- String: `starts-with?`, `ends-with?`, `contains?`, `regex?` 
- Similarity: `levenshtein`, `jaccard`, `cosine-sim`, `word2vec`
- TF-IDF scoring for text relevance

### Path System

The path function extracts values from JSON documents:
- Dot notation: `user.name`
- Array indices: `users.[3].name`
- Wildcards: `users.*.name`, `users.**.name`
- Array slicing and complex navigation

### Mathematical Properties

The system maintains a **homomorphism** between queries and result sets:
- Operations on queries translate directly to operations on fuzzy result sets
- `Φ(Q1 and Q2) = Φ(Q1) ∩ Φ(Q2)` where ∩ applies element-wise minimum
- Ensures consistency whether combining at query or result level

## Development Commands

### Installation
```bash
# Set up complete development environment
make install-dev

# Install package only
make install

# Create virtual environment
make venv

# Update dependencies
make deps
```

### Testing
```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Generate HTML coverage report
make coverage

# Run specific test file
venv/bin/pytest tests/test_specific.py

# Run tests matching pattern
venv/bin/pytest -k "test_fuzzy"
```

### Code Quality
```bash
# Run linters (ruff)
make lint

# Format code with black
make format

# Type checking with mypy
make type-check

# Run all checks (lint, type-check, test)
make check

# Pre-commit checks
make pre-commit
```

### Documentation
```bash
# Build documentation
make docs

# Serve docs locally
make docs-serve

# Clean documentation
make docs-clean
```

### Building & Distribution
```bash
# Build distribution packages
make build

# Publish to TestPyPI
make publish-test

# Publish to PyPI
make publish
```

### Development Utilities
```bash
# Launch Python shell with package imported
make shell

# Launch Jupyter notebook
make jupyter

# Update all dependencies
make update-deps

# Freeze dependencies
make freeze

# Show current version
make version
```

### Version Management
```bash
# Bump patch version (0.0.X)
make bump-patch

# Bump minor version (0.X.0) 
make bump-minor

# Bump major version (X.0.0)
make bump-major
```

### Cleanup
```bash
# Clean build artifacts
make clean

# Clean everything including venv
make clean-all
```

## Key Dependencies

- `numpy`: Numerical operations for fuzzy computations
- `scikit-fuzzy`: Fuzzy logic toolkit
- `pytest`: Testing framework
- `black`: Code formatter
- `ruff`: Fast Python linter
- `mypy`: Static type checker

## Testing Structure

Tests are in `tests/` directory:
- `fuzzy_json_query_field_path_tests.py`: Field path extraction tests
- Additional test files to be added for each module

## Integration with jaf

While `jaf` provides Boolean algebra for crisp filtering, `fuzzy-logic-search` extends this to continuous membership degrees. Key differences:

| Aspect | jaf (Boolean) | fls (Fuzzy) |
|--------|--------------|-------------|
| Results | Binary (true/false) | Continuous [0,1] |
| Logic | Crisp Boolean | Fuzzy logic with degrees |
| Modifiers | None | very, somewhat, slightly |
| Transitions | Abrupt cutoffs | Smooth gradations |
| Use Case | Exact filtering | Relevance ranking |

Consider importing jaf's efficient streaming architecture and path evaluation system while maintaining fuzzy logic semantics.

## Usage Examples

### Simple Fuzzy Query
```python
from fuzzy_logic_search import FuzzyQuery

# Create a fuzzy query
query = FuzzyQuery(["and", 
    [">=", ["path", "age"], 25],
    ["contains?", ["path", "name"], "smith"]
])

# Evaluate on documents
results = query.evaluate(documents)
# Returns FuzzySet with membership degrees
```

### With Modifiers
```python
# Very relevant matches only
strict_query = FuzzyQuery(["very", 
    ["==", ["path", "status"], "active"]
])

# More tolerant matching
tolerant_query = FuzzyQuery(["somewhat",
    ["close-match?", ["path", "city"], "New York"]
])
```

### Post-Processing Results
```python
# Combine result sets
combined = results1.union(results2)  # Fuzzy OR
filtered = results1.intersection(results2)  # Fuzzy AND

# Apply modifiers to results
emphasized = very(results)
broadened = somewhat(results)
```

## Future Enhancements

- Implement streaming evaluation inspired by jaf's lazy architecture
- Add probabilistic data structures for scalability
- Support for more complex linguistic hedges
- Integration with vector databases for semantic search
- FastAPI endpoint for REST access
- WebSocket support for real-time fuzzy queries