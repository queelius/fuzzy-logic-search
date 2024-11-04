# This is not the right approach, since it's not clear how to integrate this
# with the Boolean algebra. The idea is to use the td-idf score as the default
# score, and then allow the user to provide a custom score function.

class TdIdf:

    def __init__(self, corpus):
        self.corpus = corpus
        self.td_idf = TdIdf.generate_td_idf(corpus)

    @staticmethod
    def generate_td_idf(corpus):
        """
        Create the term-document inverse document frequency (td-idf) matrix.
        """
        # Create the term frequency matrix
        term_freq = {}
        for doc in corpus:
            for term in doc:
                term_freq[term] = term_freq.get(term, 0) + 1

        # Create the inverse document frequency matrix
        inv_doc_freq = {}
        for term in term_freq:
            inv_doc_freq[term] = len(corpus) / term_freq[term]

        # Create the td-idf matrix
        td_idf = {}
        for doc in corpus:
            for term in doc:
                td_idf[(term, doc)] = term_freq[term] * inv_doc_freq[term]

        return td_idf
    
    def __call__(self, query):
        """
        Compute the td-idf score for the query with respect to each document in the corpus.
        """
        # instantiate a dictionary to store the scores
        scores = {}
        for doc in self.corpus:
            h = hash(doc)
            for term in query:
                scores[h] = self.td_idf.get((term, doc), 0)

    

class NormalizedScore:

    def __init__(self, ranker):
        self.ranker = ranker

    def __call__(self, query, corpus):
        """
        Compute the normalized score for the query based on the ranker. It
        should return a score between 0 and 1, where 0 means no match and 1
        means a perfect match.
        """
        scores = self.ranker(query)
        max_score = max(scores)
        min_score = min(scores)
        if max_score == min_score:
            return [1.0 if score > 0 else 0.0 for score in scores]
        return [(score - min_score) / (max_score - min_score) for score in scores]
    


