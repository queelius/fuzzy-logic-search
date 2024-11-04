import re
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
import nltk
nltk.download('stopwords')


class Query:
    """
    A boolean search engine for retrieving documents based on matching terms and
    operators. The engine uses an inverted index to efficiently find matching documents.

    Theory of Boolean Algebra:

    A Boolean algebra is a set A, equipped with two binary operations `and`
    and `or`, a unary operation `not`, and two elements 0 and 1 in A, such that
    for all elements `a`, `b` and `c` of A, the usual axioms of Boolean algebra hold,
    such as commutativity, associativity, and absorption laws. We denote this
    Boolean algebra as A = {0, 1, and, or, not}.

    The Boolean queries are a Boolean Algebra
    
        Q = (P(T*), and, or, not, {}, T*)
        
    where T is the set of all ASCII characters, T* is the set of all strings of
    ASCII characters, {} is the empty set, and P(T*) is the power set of T*.

    This allows us to construct queries such as:

        - "(OR (AND cat dog) (NOT (OR fish bird)))"
    """
    def __init__(self, query: str):
        self.tokens = self._tokenize_query(query)

    def _tokenize_query(self, query):
        """Tokenize and stem the query."""
        tokens = re.findall(r'\b\w+\b|\(|\)', query)
        return [self.stemmer.stem(token) for token in tokens]

    def __and__(self, other: 'Query'):
        return f"(and {self.tokens} {other.tokens})"
    
    def __or__(self, other: 'Query'):
        return f"(or {self.tokens} {other.tokens})"
    
    def __invert__(self):
        return f"(not {self.tokens})"
    
    def __repr__(self):
        # map the list of tokens | lists to a string
        return f"{' '.join(self.tokens)}"
    
    def __str__(self):
        return self.__repr__()



class BooleanSearchEngine:
    """
    A boolean search engine for retrieving documents based on matching terms and
    operators. The engine uses an inverted index to efficiently find matching documents.

    Theory of Boolean Algebra:

    A Boolean algebra is a set A, equipped with two binary operations `and`
    and `or`, a unary operation `not`, and two elements 0 and 1 in A, such that
    for all elements `a`, `b` and `c` of A, the usual axioms of Boolean algebra hold,
    such as commutativity, associativity, and absorption laws. We denote this
    Boolean algebra as A = {0, 1, and, or, not}.

    The Boolean queries are a Boolean Algebra
    
        Q = (P(T*), and, or, not, {}, T*)
        
    where T is the set of all ASCII characters, T* is the set of all strings of
    ASCII characters, {} is the empty set, and P(T*) is the power set of T*.

    This allows us to construct queries such as:

        - "(OR (AND cat dog) (NOT (OR fish bird)))"

    

    

    



        
    """
    def __init__(self,
                 docs,
                 stemmer=None,
                 stopwords_list=None):
        
        # Initialize components with defaults if not provided
        self.stemmer = stemmer or PorterStemmer()
        self.stopwords = set(stopwords_list or stopwords.words('english'))
        
        # Preprocess documents
        self.processed_docs = [' '.join(self._preprocess(doc)) for doc in docs]
        self.original_docs = docs
        
        # Build Inverted Index for Boolean Search
        self.inverted_index = self._build_inverted_index(self.processed_docs)
        self.num_docs = len(docs)
        self.all_docs_set = set(range(self.num_docs))
    
    def _preprocess(self, text):
        """Preprocess the text by removing punctuation, lowercasing, removing stopwords, and stemming."""
        text = re.sub(r'[^\w\s]', '', text).lower()
        words = text.split()
        filtered_words = [self.stemmer.stem(word) for word in words if word not in self.stopwords]
        return filtered_words
    
    def _tokenize_query(self, query):
        """Tokenize and stem the query."""
        tokens = re.findall(r'\b\w+\b|\(|\)', query)
        return [self.stemmer.stem(token) for token in tokens]
    
       
    def _build_inverted_index(self, processed_docs):
        """Build an inverted index mapping terms to the set of document indices containing them."""
        inverted = {}
        for idx, doc in enumerate(processed_docs):
            terms = set(doc.split())  # Split the doc into words
            for term in terms:
                if term in inverted:
                    inverted[term].add(idx)
                else:
                    inverted[term] = {idx}
        return inverted
    
    def _search(self, tokens):
        """Recursively process the tokens to compute the final set of matching documents."""
        if not tokens:
            raise ValueError("Unexpected end of query.")
        
        operator = tokens.pop(0).upper()
        if operator not in {'AND', 'OR', 'NOT'}:
            raise ValueError(f"Invalid operator: {operator}")
        
        operands = []
        while tokens and tokens[0] != ')':
            if tokens[0] == '(':
                tokens.pop(0)  # Remove '('
                operands.append(self._recursive_boolean_search(tokens))
            else:
                term = tokens.pop(0)
                operands.append(self.inverted_index.get(term, set()))
        
        if not tokens:
            raise ValueError("Mismatched parentheses in query.")
        tokens.pop(0)  # Remove ')'
        
        if operator == 'AND':
            return set.intersection(*operands) if operands else set()
        elif operator == 'OR':
            return set.union(*operands) if operands else set()
        elif operator == 'NOT':
            if len(operands) != 1:
                raise ValueError("NOT operator requires exactly one operand.")
            return self.all_docs_set - operands[0]
        else:
            raise ValueError(f"Invalid operator: {operator}")

       
    def search(self, query: str, scored=False) -> list:
        """
        Perform a boolean search based on exact term matching.

        :param query: The query string containing terms and operators.
        :param scored: Whether to return scores (1 for matching documents, 0 for others) or
                       just the matching document indices. The scored result can
                       be used to  combine multiple search results or transform
                       a single result using the scores, e.g., taking the
                       complement of the scores to get the NOT operation.

        """
        tokens = self._tokenize_query(query)
        if not tokens or tokens.pop(0) != '(':
            raise ValueError("Query must start with '('.")
        
        matching = self._search_(tokens)
        if scored:
            return [1.0 if idx in matching else 0.0 for idx in range(self.num_docs)]
        else:      
            return matching

