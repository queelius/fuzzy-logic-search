import re
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
import nltk
nltk.download('stopwords')

class FuzzySearchEngine:
    def __init__(self, docs, stemmer=None, vectorizer=None, stopwords_list=None):
        # Initialize components with defaults if not provided
        self.stemmer = stemmer or PorterStemmer()
        self.vectorizer = vectorizer or TfidfVectorizer()
        self.stopwords = set(stopwords_list or stopwords.words('english'))
        
        # Preprocess documents
        processed_docs = [' '.join(self._preprocess(doc)) for doc in docs]
        self.original_docs = docs
        self.doc_vectors = self.vectorizer.fit_transform(processed_docs).toarray().tolist()
    
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
    
    def _compute_term_scores(self, term):
        """Compute the score for each document based on the term's vector."""
        term_vector = self.vectorizer.transform([term]).toarray()[0].tolist()
        return [
            sum(doc_val * term_val for doc_val, term_val in zip(doc_vec, term_vector))
            for doc_vec in self.doc_vectors
        ]
    
    def _search(self, tokens):
        """Recursively process the tokens to compute the final scores."""
        if not tokens:
            raise ValueError("Unexpected end of query.")
        
        operator = tokens.pop(0).upper()
        if operator not in {'AND', 'OR', 'NOT'}:
            raise ValueError(f"Invalid operator: {operator}")
        
        operands = []
        while tokens and tokens[0] != ')':
            if tokens[0] == '(':
                tokens.pop(0)  # Remove '('
                operands.append(self._search(tokens))
            else:
                term = tokens.pop(0)
                operands.append(self._compute_term_scores(term))
        
        if not tokens:
            raise ValueError("Mismatched parentheses in query.")
        tokens.pop(0)  # Remove ')'
        
        if operator == 'AND':
            # Element-wise minimum for AND operation
            return [min(scores) for scores in zip(*operands)]
        elif operator == 'OR':
            # Element-wise maximum for OR operation
            return [max(scores) for scores in zip(*operands)]
        elif operator == 'NOT':
            if len(operands) != 1:
                raise ValueError("NOT operator requires exactly one operand.")
            # Simple NOT implementation: invert scores (assuming scores are between 0 and 1)
            return [1 - score for score in operands[0]]
    
    def search(self, query):
        """Search the documents based on the algebraic query."""
        tokens = self._tokenize_query(query)
        if not tokens or tokens.pop(0) != '(':
            raise ValueError("Query must start with '('.")
        
        scores = self._search(tokens)
        return scores

