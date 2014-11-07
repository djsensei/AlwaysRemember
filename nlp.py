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
import pandas as pd

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

def clean_these_docs(table, docs):
    '''
    Cleans just the documents in this list
    '''
    pass

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
    cursor = table.find(q)
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

def initial_topic_pipeline(table, query, max_features=20000, ngram_range=(1, 3),
                           max_df=.8, n_topics=30, n_top_words=30):
    '''
    Runs the 9/11 corpus through TFIDF->NMF, printing the topics for human
        inspection and analysis.
    After inspection, create a vector of topic relevance weights and feed it
        into final_topic_pipeline along with article_relevance.
    '''
    X, vec, article_ids = table_tfidf(table, query, max_features, ngram_range,
                                      max_df)
    W, H = basic_nmf(X, n_topics)
    topic_dicts = topic_parse(vec, H, n_topics, n_top_words)
    print_topics(topic_dicts)
    return W, article_ids, topic_dicts

def final_topic_pipeline(table, query, article_relevance, relevance_threshold,
                         max_features=50000, ngram_range=(1, 3), max_df=.8,
                         n_topics=20, n_top_words=30):
    '''
    Using article_relevance and some relevance_threshold, filter out documents
        from the query that aren't relevant. Using only the cleared relevant
        documents, retrain the TFIDF-NMF model. Print the new topics out for
        naming (and reweighting, if necessary).
    '''
    clear_df = pd.DataFrame(article_relevance)
    clear_df.columns = ['_id', 'relevance']

    q = {'clean_text': {'$exists': True}}
    for k, v in query.iteritems():
        q[k] = v
    cursor = table.find(q)
    query_df = pd.DataFrame([(c['_id'], c['clean_text']) for c in cursor])
    query_df.columns = ['_id', 'clean_text']

    bigdf = pd.merge(clear_df, query_df, on='_id')
    bigdf['relevance'] = bigdf['relevance'].astype(float)
    condition = bigdf['relevance'] >= relevance_threshold

    vec = TfidfVectorizer(max_features=max_features, ngram_range=ngram_range,
                          max_df=max_df)
    X = vec.fit_transform(bigdf[condition]['clean_text'].values)

    W, H = basic_nmf(X, n_topics)
    topic_dicts = topic_parse(vec, H, n_topics, n_top_words)
    print_topics(topic_dicts)
    return vec, H, topic_dicts

def article_topic_strength(W, article_ids, topic_relevance,
                           pre_vectorized=False):
    '''
    Determines how much each article relates to the topics extracted from NMF.
    topic_relevance is user-generated from the topics, and looks like this:
        {index: ['name', weight]}.
    If topic_relevance is already just a vector of weights: pre_vectorized!
    '''
    if not pre_vectorized:
        topic_relevance_vector = np.array([v[1] for k,v in \
                                       topic_relevance.iteritems()])
        article_relevance = W.dot(topic_relevance_vector.T)
    else:
        article_relevance = W.dot(topic_relevance.T)
    return zip(article_ids, article_relevance)

def print_topics(topic_dicts):
    for i, topic in enumerate(topic_dicts):
        l = sorted(topic.items(), key=lambda x: x[1])[::-1]
        print "Topic #" + str(i)
        for item in l:
            print '  ', item[1], '  ', item[0]
        print '\n'
