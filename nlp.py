'''
NLP functionality for Timescape project
'''
from string import punctuation
from nltk.corpus import stopwords
from nltk.util import ngrams
from nltk.tokenize import word_tokenize
from pymongo import MongoClient
from collections import Counter
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

additional_stopwords = ['said']

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
    stops = stopwords.words('english') + additional_stopwords
    doc = str(''.join([i if ord(i) < 128 else ' ' for i in doc])).lower()
    doc = doc.translate(None, punctuation)
    t = word_tokenize(doc)
    clean = []
    for word in t:
        if word not in stops:
            clean.append(word)
    return clean

def clean_all_docs(table):
    '''
    Takes all documents in a table, cleans them with tokenize, and adds the
        clean document back into their record as 'clean_text'
    '''
    for record in table.find({'full_text': {'$exists': True, '$ne': ''}}):
        clean_doc = ' '.join(tokenize(record['full_text']))
        table.update({'web_url': record['web_url']},
                     {'$set': {'clean_text': clean_doc}},
                     upsert=True)

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
                vocab[n+1][' '.join(g)] += 1
    return {i:vocab[i].most_common(topn) for i in vocab}

def table_tfidf(table, max_features=5000, ngram_range=(1, 1), max_df=.8):
    vec = TfidfVectorizer(max_features=max_features,
                            ngram_range=ngram_range,
                            max_df=max_df)
    X = vec.fit_transform([r['clean_text'] for r in table.find({'clean_text': \
                                                        {'$exists': True}})])
    return X, vec

def basic_nmf(X, n_topics=20):
    nmf = NMF(n_components=n_topics)
    W = nmf.fit_transform(X)
    H = nmf.components_
    return W, H

def topic_parse(X, vec, H, n_topics=20, n_top_words=20):
    topics_dicts = []

    for i in xrange(n_topics):
        k, v = zip(*sorted(zip(vec.get_feature_names(), H[i]),
                               key=lambda x: x[1])[:-n_top_words:-1])
        val_arr = np.array(v)
        norms = val_arr / np.sum(val_arr)
        topics_dicts.append(dict(zip(k, np.rint(norms * 300))))
    return topics_dicts

def tfidf_nmf_analyze(table, max_features, ngram_range, max_df, n_topics,
                      n_top_words):
    '''
    Combines the TFIDF -> NMF -> Topic Modeling pipeline into one function
    '''
    X, vec = table_tfidf(table, max_features, ngram_range, max_df)
    W, H = basic_nmf(X, n_topics)
    topic_dicts = topic_parse(X, vec, H, n_topics, n_top_words)

    for i, topic in enumerate(topic_dicts):
        print "Topic #" + str(i)
        print sorted(topic.items(), key=lambda x: x[1])[::-1]
        print '\n'
