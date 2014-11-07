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

additional_stopwords = ['said', 'would', 'like', 'many', 'also', 'could',
                        'mr', 'ms', 'mrs', 'may', 'even','say', 'much',
                        'going', 'might', 'dont', 'go', 'another', 'around',
                        'says', 'editor']
all_stopwords = set(stopwords.words('english') + additional_stopwords)

def get_raw_docs(table):
    '''
    Gets just the raw docs from a table, no labels or anything.
    '''
    docs = []
    for record in table.find({'full_text': {'$exists': True}}):
        docs.append(record['full_text'])
    return docs

def clean_tokenize(doc):
    '''
    Tokenizes a document into a bag of words.
    '''
    doc = str(''.join([i if ord(i) < 128 else ' ' for i in doc])).lower()
    doc = doc.translate(None, punctuation)
    t = word_tokenize(doc)
    clean = []
    for word in t:
        if word not in all_stopwords:
            clean.append(word)
    return clean

def clean_all_docs(table, overwrite=False, verbose=False):
    '''
    Takes all documents in a table, cleans them with tokenize, and adds the
        clean document back into their record as 'clean_text'. Overwrite
        specifies whether or not to clean documents that already have a
        clean_text element (say, if you've updated the tokenizer).
    '''
    mongo_query = {'full_text': {'$exists': True, '$ne': ''}}
    if not overwrite:
        mongo_query['clean_text'] = {'$exists':False}
    i = 0
    total_count = table.find(mongo_query).count()
    print 'cleaning ', total_count, ' docs...'
    for record in table.find(mongo_query):
        i += 1
        if verbose and i % 500 == 0:
            print 'cleaning doc # ', i
        try:
            clean_doc = ' '.join(clean_tokenize(record['full_text']))
        except:
            print 'failed to tokenize record: id ', record['_id']
            continue
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
        d = clean_tokenize(document)
        for word in d:
            vocab[1][word] += 1
        for n in range(1, nmax):
            for g in ngrams(d, n+1):
                vocab[n+1][' '.join(g)] += 1
    return {i:vocab[i].most_common(topn) for i in vocab}

def table_tfidf(table, query={}, max_features=5000, ngram_range=(1, 1),
                max_df=.8):
    vec = TfidfVectorizer(max_features=max_features,
                            ngram_range=ngram_range,
                            max_df=max_df)
    q = {'clean_text': {'$exists': True}}
    for k, v in query.iteritems():
        q[k] = v
    cursor = table.find(query)
    articles = [(c['_id'], c['clean_text']) for c in cursor]
    article_ids = [a[0] for a in articles]
    article_text = [a[1] for a in articles]
    X = vec.fit_transform(article_text)
    return X, vec, article_ids

def basic_nmf(X, n_topics=20):
    nmf = NMF(n_components=n_topics)
    W = nmf.fit_transform(X)
    H = nmf.components_
    return W, H

def topic_parse(vec, H, n_topics=20, n_top_words=20):
    topics_dicts = []

    for i in xrange(n_topics):
        k, v = zip(*sorted(zip(vec.get_feature_names(), H[i]),
                               key=lambda x: x[1])[:-n_top_words:-1])
        val_arr = np.array(v)
        norms = val_arr / np.sum(val_arr)
        topics_dicts.append(dict(zip(k, np.rint(norms * 300))))
    return topics_dicts

def tfidf_nmf_analyze(table, query, max_features, ngram_range, max_df, n_topics,
                      n_top_words):
    '''
    Combines the TFIDF -> NMF -> Topic Modeling pipeline into one function
    '''
    X, vec, article_ids = table_tfidf(table, query, max_features, ngram_range, max_df)
    W, H = basic_nmf(X, n_topics)
    topic_dicts = topic_parse(vec, H, n_topics, n_top_words)
    return topic_dicts, article_ids

def article_topic_strength(W, article_ids, topic_relevance_dict):
    '''
    Determines how much each article relates to the topics extracted from NMF.
    topic_relevance_dict is user-generated from the topics, and looks like this:
        {index: ['name', weight]}
    '''
    topic_relevance_vector = np.array([v[1] for k,v in \
                                       topic_relevance_dict.iteritems()])
    article_relevance = W.dot(topic_relevance_vector.T)
    return article_relevance

def print_topics(topic_dicts):
    for i, topic in enumerate(topic_dicts):
        l = sorted(topic.items(), key=lambda x: x[1])[::-1]
        print "Topic #" + str(i)
        for item in l:
            print '  ', item[1], '  ', item[0]
        print '\n'
