'''
NLP functionality for Timescape project
'''
from string import punctuation
from nltk.corpus import stopwords
from nltk.util import ngrams
from nltk.tokenize import word_tokenize
from pymongo import MongoClient
from collections import Counter

def get_raw_docs(table):
    '''
    Gets just the raw docs from a table, no labels or anything.
    '''
    docs = []
    for record in table.find({'full_text': {'$exists': True}}):
        docs.append(record['full_text'])
    return docs

def tokenize(doc):
    '''
    Tokenizes a document into a bag of words.
    '''
    stops = stopwords.words('english')
    doc = str(''.join([i if ord(i) < 128 else ' ' for i in doc])).lower()
    doc = doc.translate(None, punctuation)
    t = word_tokenize(doc)
    clean = []
    for word in t:
        if word not in stops:
            clean.append(word)
    return clean

def simple_cluster(docs, nmax=1, topn=20):
    '''
    Returns the most common n-grams in the list of docs, from 1 to nmax
    '''
    vocab = {}
    for i in range(nmax):
        vocab[i+1] = Counter()
    for document in docs:
        d = tokenize(document)
        for word in d:
            vocab[1][word] += 1
        for n in range(1, nmax):
            for g in ngrams(d, n+1):
                vocab[n+1][g] += 1
    return {i:vocab[i].most_common(topn) for i in vocab}
