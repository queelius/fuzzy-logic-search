```python

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
import nltk
import numpy as np
import re
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords

class AlgebraicSearchEngine:
    def __init__(self,
                 docs : list[str],
                 stemmer=PorterStemmer(),
                 vectorizer=TfidfVectorizer(),
                 stopwords=stopwords.words('english')):

        self.stemmer = stemmer
        self.vectorizer = vectorizer
        self.stopwords = stopwords

        proc_docs = []
        for doc in docs:
            proc_tokens = self.process_doc(doc)
            proc_doc = ' '.join(proc_tokens)
            # Add the stemmed document to the list of stemmed documents
            proc_docs.append(proc_doc)

        # Store the original and processed documents
        self.docs = docs
        # Store the processed document vectors
        self.vecs = self.vectorizer.fit_transform(proc_docs).toarray()

    def process_query(self, query: str) -> list[str]:
        tokens = re.findall(r'\b\w+\b|\(|\)', query)
        tokens = [self.stemmer.stem(token) for token in tokens]
        return tokens

    def process_doc(self, doc : str) -> list[str]:
        # remove punctuation
        doc = re.sub(r'[^\w\s]', '', doc)
        # lower-case
        doc = doc.lower()
        # split the string into words
        words = doc.split()
        # remove stopwords
        words = [word for word in words if word not in self.stopwords]
        # stem each word and join them back into a string
        words = [self.stemmer.stem(word) for word in words]
        return words

    def recursive_search(self, tokens):
        operator = tokens.pop(0).upper()

        if operator not in ['AND', 'OR', 'NOT']:
            raise ValueError(f"Invalid operator {operator}")
        
        operands = []
        while tokens[0] != ')':
            if tokens[0] == '(':
                tokens.pop(0)  # Remove '('
                operands.append(self.recursive_search(tokens))
            else:
                term_vec = self.vectorizer.transform([tokens.pop(0)]).toarray()[0]
                term_scores = self.vecs.dot(term_vec)
                operands.append(term_scores)

        tokens.pop(0)  # Remove ')'
        result = None
        if operator == 'AND':
            result = np.min(np.array(operands), axis=0)
        elif operator == 'OR':
            result = np.max(np.array(operands), axis=0)
        elif operator == 'NOT':
            if len(operands) != 1:
                raise ValueError("NOT operator can only have one operand")
            result = 1 - operands[0]
        return result
    
    def search(self, query) -> np.ndarray:
        tokens = self.process_query(query)
        if tokens[0] != '(':
            raise ValueError("Invalid query")
        
        tokens = tokens[1:]

        scores = self.recursive_search(tokens)
        return scores

```


```python
docs = ["The cat in the hat",
        "This is just a document with no other purpose than to show how the search engine works.",
        "A dog and his boy.",
        "A boy jumps up and down.",
        "The cats are out of the bag.",
        "Dogs and cats, living together.",
        "The quick brown fox jumps over the lazy dog.",
        "Cats, cats, cats, cats, cats, and maybe a dog!",
        "The dog did not bite the cat.",
        "The quick brown dog jumps over the lazy cat.",
        "The super fast brown dog jumps over the lazy cat.",
        "The dog brown dog jumps over the lazy cat.",
        "a quick dog bite a cat",
        "dog cat",
        "quick dog",
        "Dog, dogs, dogs, dogs, dogs! And maybe a cat.",
        "Dog, dogs, dogs! And maybe a cat.",
        "Okay, now is the time, for all the good men, to come to the aid of their country.",
        "Cat cat cat cat cat cat cats cats cats!",
        "test"]
boolean_search_engine = AlgebraicSearchEngine(
    docs=docs,
    vectorizer=CountVectorizer(binary=True))

boolean_search_engine.process_doc("Dogs and cats, living together!!!")
# Document: "Dogs and cats, living together!!!",
#   boolean_search_engine.process_doc("Dogs and cats, living together!!!")
#   -> pre-processed: ['dogs', 'and', 'cats', 'living', 'together']
#   -> stop-words removed: ['dogs', 'cats', 'living', 'together']
#   -> stemmed words: ['dog', 'cat', 'live', 'togeth']
```




    ['dog', 'cat', 'live', 'togeth']



Now we show how a query is processed. Recall the query permits `AND`, `OR`, and
`NOT`, which is sufficient to implement a Boolean algebra. In particular, this
means that given a query, a subset of the documents is denoted by the query.

We imagine that the Boolean algebra is over the powerset of the words in the
all the documents. A query is a special way of specifying a subset of the
powerset of the words in the documents. The subset is specified by the
occurrence of the words in the query. For example, the query `A AND B` denotes
the set of documents that contain both `A` and `B`. The query `A OR B` denotes
the set of documents that contain either `A` or `B`. The query `NOT A` denotes
the set of documents that do not contain `A`. We may combine these to form
complex queries. For example, the query `A AND (B OR NOT C) AND NOT D` denotes the
set of documents that contain `A` and either `B` or not `C` and do not contain
`D`.

A document is said to be relevant to a query if it is in the subset denoted by
the query. The goal of the search engine is to return the documents that are
relevant to the query.


```python
query = "(AND cat dog (NOT bite) (OR quick fast))"
print(f"Query: {query}")
# Query: (AND cat (NOT bite) dog (AND dog (OR quick fast)) (NOT boy))
print(f'Processed query: {boolean_search_engine.process_query(query)}')
# Processed query: ['(', 'and', 'cat', '(', 'not', 'bite', ')', 'dog', '(', 'and', 'dog', '(', 'or', 'quick', 'fast', ')', ')', '(', 'not', 'boy', ')', ')'

print("Boolean search")
scores = boolean_search_engine.search(query)
print(f"Scores: {scores}")

```

    Query: (AND cat (NOT bite) dog (AND dog (OR quick fast)) (NOT boy))
    Processed query: ['(', 'and', 'cat', '(', 'not', 'bite', ')', 'dog', '(', 'and', 'dog', '(', 'or', 'quick', 'fast', ')', ')', '(', 'not', 'boy', ')', ')']
    Boolean search
    Scores: [0 0 0 0 0 0 0 0 0 1 1 0 0 0 0 0 0 0 0 0]


Now we show the relevant results.


```python
results = boolean_search_engine.search(query)
# Only print the documents that have a score > 0
res = [i for i in np.where(results > 0)[0]]
# retrieve the original documents
for i in res:
    print(f"Document {i}: {docs[i]}")
```

    Document 9: The quick brown dog jumps over the lazy cat.
    Document 10: The fast brown dog jumps over the lazy cat.


Now we use TF-IDF to score the words in the text. We will use the TfidfVectorizer from the scikit-learn library to convert the text into a matrix of TF-IDF features. We will then use the cosine similarity to find the similarity between the text and the query.


```python
fuzzy_search_engine = AlgebraicSearchEngine(docs=docs, vectorizer=TfidfVectorizer())
results = fuzzy_search_engine.search(query)
print(f"Scores: {results}")

for i, score in enumerate(results):
    print(f"Document {i}: {docs[i]} - Score: {score}")

```

    Scores: [0.         0.         0.         0.         0.         0.
     0.         0.         0.         0.27141578 0.24800208 0.
     0.3161736  0.         0.         0.         0.         0.
     0.         0.        ]


Let's show the results, from most to least relevant. We'll put them in
a list of tuples, `(index, score)`, where `index` is the index of the document
in the list of documents and `score` is the score of the document.


```python
# let's put the list in the form (i, score) and sort it
res = sorted(enumerate(results), key=lambda x: x[1], reverse=True)
for i, score in res:
    print(f"Document {i}: {docs[i]} ({score})")
```

    Document 12: a quick dog bite a cat (0.3161735956168409)
    Document 9: The quick brown dog jumps over the lazy cat. (0.2714157795710721)
    Document 10: The fast brown dog jumps over the lazy cat. (0.24800207957278061)
    Document 0: The cat in the hat (0.0)
    Document 1: This is just a document with no other purpose than to show how the search engine works. (0.0)
    Document 2: A dog and his boy. (0.0)
    Document 3: A boy jumps up and down. (0.0)
    Document 4: The cats are out of the bag. (0.0)
    Document 5: Dogs and cats, living together. (0.0)
    Document 6: The quick brown fox jumps over the lazy dog. (0.0)
    Document 7: Cats, cats, cats, cats, cats, and maybe a dog! (0.0)
    Document 8: The dog did not bite the cat. (0.0)
    Document 11: The dog brown dog jumps over the lazy cat. (0.0)
    Document 13: dog cat (0.0)
    Document 14: quick dog (0.0)
    Document 15: Dog, dogs, dogs, dogs, dogs! And maybe a cat. (0.0)
    Document 16: Dog, dogs, dogs! And maybe a cat. (0.0)
    Document 17: Okay, now is the time, for all the good men, to come to the aid of their country. (0.0)
    Document 18: Cat cat cat cat cat cat cats cats cats! (0.0)
    Document 19: test (0.0)

