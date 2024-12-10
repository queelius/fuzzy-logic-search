import os
import re
import logging

logging.basicConfig(level=logging.INFO)

class Corpus:
    """
    A class to represent a corpus of documents.

    The corpus models the concept of a set (of documents) and provides methods
    for loading documents from a directory, adding and removing documents, and
    performing set operations on corpora.

    Attributes:
        corpus (dict): A dictionary containing the documents in the corpus.
            It is a key-value pair where the key is the filename and the value is
            another dictionary containing the metadata and content of the document.
            The value dictionary for each document has the following structure:
            ```
            {
                'filename': {
                    'metadata': {
                        'filename': 'filename',
                        'path': 'path',
                        'size': 'size',
                        'extension': 'extension',
                        'created': 'created',
                        'modified': 'modified',
                        'accessed': 'accessed',
                        'owner': 'owner',
                        'group': 'group',
                        'permissions': 'permissions'
                    },
                    'content': 'content'
                }
            }
            ```
        encoding (str): The encoding to use when reading the files in the corpus.
        regex_ext (str): A regular expression pattern to match the file extensions
            of the documents to include in the corpus. By default, it matches all
            file extensions.

    """
    def __init__(self,
                 encoding='latin-1',
                 regex_ext='.*'):
        self.corpus = dict()
        self.default_regex_ext = regex_ext
        self.encoding = encoding

    def __len__(self):
        return len(self.corpus)
    
    def __getitem__(self, key):
        return self.corpus[key]
    
    def __iter__(self):
        return iter(self.corpus)
    
    def __contains__(self, key):
        return key in self.corpus
    
    def clear(self):
        self.corpus.clear()

    def __str__(self):
        if len(self.corpus) == 0:
            return "Corpus([])"
        elif len(self.corpus) <= 5:
            return f"Corpus({self.corpus.keys()})"
        else:
            return f"Corpus({self.corpus.keys()[:3]}...)"
    
    def __repr__(self):
        return f"Corpus({self.corpus})"
    
    def __eq__(self, other):
        return set(self.corpus) == set(other.corpus)
    
    def __ne__(self, other):
        return set(self.corpus) != set(other.corpus)
    
    def __sub__(self, other):
        new_corpus = Corpus()
        new_corpus.corpus = {k: v for k, v in self.corpus.items() if k not in other.corpus}
        return new_corpus
    
    def __and__(self, other):
        new_corpus = Corpus()
        new_corpus.corpus = {k: v for k, v in self.corpus.items() if k in other.corpus}
        return new_corpus
    
    def __or__(self, other):
        new_corpus = Corpus()
        new_corpus.corpus = {**self.corpus, **other.corpus}
        return new_corpus
    
    def __xor__(self, other):
        new_corpus = Corpus()
        new_corpus.corpus = {k: v for k, v in self.corpus.items() if k not in other.corpus}
        new_corpus.corpus.update({k: v for k, v in other.corpus.items() if k not in self.corpus})
        return new_corpus
    
    def add(self, filename, content, metadata=None):
        """
        Add a document to the corpus.

        Args:
            filename (str): The name of the document.
            content (str): The content of the document.
            metadata (dict, optional): Additional metadata for the document.
        """
        if filename in self.corpus:
            logging.warning('File {} already exists in the corpus. Skipping...'.format(filename))
        self.corpus[filename] = {
            'metadata': metadata,
            'content': content
        }

    def remove(self, filename):
        """
        Remove a document from the corpus.

        Args:
            filename (str): The name of the document to remove.
        """
        if filename in self.corpus:
            del self.corpus[filename]
        else:
            logging.warning('File {} not found in the corpus. Skipping...'.format(filename))
    
    def clear(self):
        self.corpus.clear()

    def load(self, path, recursively=True, followlinks=False):
        """
        Load a corpus from a directory.

        Args:
            path (str): The path to the directory containing the corpus files.
            recursively (bool): Whether to load files recursively from
                subdirectories (default: True).
        """
        for root, _, files in os.walk(path, topdown=recursively,
                                      followlinks=followlinks):
            for file in files:
                ext = os.path.splitext(file)[1]
                if re.match(self.regex_ext, ext):        
                    with open(os.path.join(root, file), 'r',
                              encoding=self.encoding) as f:
                        # Read the file content
                        content = f.read()
                        # Save the file content and metadata in the dictionary
                        if file in self.corpus:
                            logging.warning('File {} already exists in the corpus. Skipping...'.format(file))
                        self.corpus[file] = {
                            'metadata': {
                                'filename': file,
                                'path': os.path.join(root, file),
                                'size': os.path.getsize(os.path.join(root, file)),
                                'extension': ext,
                                'created': os.path.getctime(os.path.join(root, file)),
                                'modified': os.path.getmtime(os.path.join(root, file)),
                                'accessed': os.path.getatime(os.path.join(root, file)),
                                'owner': os.stat(os.path.join(root, file)).st_uid,
                                'group': os.stat(os.path.join(root, file)).st_gid,
                                'permissions': os.stat(os.path.join(root, file)).st_mode
                            },
                            'content': content
                        }
                        