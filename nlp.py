'''
Natural Language Processing functionality for the Always Remember project.

Dan Morris 11/3/14 - 11/20/14
'''
from string import punctuation
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from pymongo import MongoClient
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import pandas as pd

ADDITIONAL_STOPWORDS = ['said', 'would', 'like', 'many', 'also', 'could',
                        'mr', 'ms', 'mrs', 'may', 'even', 'say', 'much',
                        'going', 'might', 'dont', 'go', 'another', 'around',
                        'says', 'editor']
ALL_STOPWORDS = set(stopwords.words('english') + ADDITIONAL_STOPWORDS)


def clean_tokenize(doc):
    '''
    Cleans a document of stopwords, symbols, and punctuation.

    INPUT:  string - dirty document
    OUTPUT: string - clean document!
    '''
    doc = str(''.join([i if ord(i) < 128 else ' ' for i in doc])).lower()
    doc = doc.translate(None, punctuation)
    t = word_tokenize(doc)
    clean = []
    for word in t:
        if word not in ALL_STOPWORDS:
            clean.append(word)
    return clean


def clean_these_docs(table, records, verbose=False):
    '''
    Cleans all documents in this list of records, adding the clean
        version back into the record. Generally used during an
        active scrape.

    INPUT:  mongo-collection - table, list - document record dicts,
            bool - verbose
    OUTPUT: None
    '''
    i = 0
    for r in records:
        i += 1
        if verbose and i % 100 == 0:
            print 'cleaning doc # ', i
        try:
            full_text = table.find_one({'_id': r['_id']})['full_text']
            clean_text = ' '.join(clean_tokenize(full_text))
            table.update({'_id': r['_id']},
                         {'$set': {'clean_text': clean_text}},
                         upsert=True)
        except:
            print 'failed to tokenize record: id ', r['_id']


def clean_all_docs(table, overwrite=False, verbose=False):
    '''
    Cleans all documents in the table and inserts the clean version into
        the record. Defaults to only process docs without an existing
        clean version. Toggle 'overwrite' to guarantee that all docs
        in the table are cleaned.

    INPUT:  mongo-collection - table, bool - overwrite, bool - verbose
    OUTPUT: None
    '''
    mongo_query = {'full_text': {'$exists': True, '$ne': ''},
                   'type_of_material': 'News'}
    if not overwrite:
        mongo_query['clean_text'] = {'$exists': False}
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


def docs_tfidf(clean_articles, max_features=5000, ngram_range=(1, 1),
               max_df=.8):
    '''
    Builds a TF-IDF vectorizer using a list of clean article strings.

    INPUT:  list - clean_articles, int - max_features,
            tuple - ngram_range, float - max_df
    OUTPUT: 2d sparse numpy array - X feature matrix,
            vectorizer object - vec
    '''
    vec = TfidfVectorizer(max_features=max_features,
                          ngram_range=ngram_range,
                          max_df=max_df)
    X = vec.fit_transform(articles)
    return X, vec


def table_tfidf(table, query={}, max_features=5000, ngram_range=(1, 1),
                max_df=.8):
    '''
    Builds a TF-IDF vectorizer using records in the table which match
        the input query.

    INPUT:  mongo-collection - table, dict - query, int - max_features,
            tuple - ngram_range, float - max_df
    OUTPUT: 2d sparse numpy array - X feature matrix,
            vectorizer object - vec,
            list - article_ids corresponding to row indices of matrix
    '''
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


def basic_nmf(X, n_topics=20, **kwargs):
    '''
    Performs NMF on the TF-IDF feature matrix to create a topic model.

    INPUT:  2d numpy array - X, int - n_topics, **kwargs for NMF parameters
    OUTPUT: 2d numpy array - W (Article-Topic matrix),
            2d numpy array - H (Topic-Term matrix)
    '''
    nmf = NMF(n_components=n_topics, **kwargs)
    W = nmf.fit_transform(X)
    H = nmf.components_
    return W, H


def topic_parse(vec, H, n_top_words=20):
    '''
    Connects actual terms and n-grams to the features of each topic
        for visualization.

    INPUT:  vectorizer object - vec, 2d numpy array - H, int - n_top_words
    OUTPUT: dict - topics_dicts (most important terms for each topic)
    '''
    topics_dicts = []
    n_topics = H.shape[0]

    for i in xrange(n_topics):
        k, v = zip(*sorted(zip(vec.get_feature_names(), H[i]),
                           key=lambda x: x[1])[:-n_top_words:-1])
        val_arr = np.array(v)
        norms = val_arr / np.sum(val_arr)
        topics_dicts.append(dict(zip(k, norms * 100)))
    return topics_dicts


def initial_topic_pipeline(table, query, max_features=20000,
                           ngram_range=(1, 3), max_df=.8, n_topics=30,
                           n_top_words=30):
    '''
    Runs the 9/11 corpus through TF-IDF->NMF. Prints the resulting topics
        for human inspection/analysis and outputs the relevant objects
        for the next step in the pipeline (filtering irrelevant documents
        and re-fitting TF-IDF and NMF).

    INPUT:  mongo-collection - table, dict - mongo query,
            int - max_features, tuple - ngram_range, float - max_df,
            int - n_topics, int - n_top_words
    OUTPUT: 2d numpy array - W, list - article_ids, list - topic_dicts
    '''
    X, vec, article_ids = table_tfidf(table, query, max_features, ngram_range,
                                      max_df)
    W, H = basic_nmf(X, n_topics)
    topic_dicts = topic_parse(vec, H, n_top_words)
    print_topics(topic_dicts)
    return W, article_ids, topic_dicts


def article_topic_strength(W, article_ids, topic_relevance):
    '''
    Determines how much each article relates to the NMF topics.
    topic_relevance is user-generated from the topics, and looks like this:
        {index: ['name', weight]}.
    If topic_relevance is already just a vector of weights: pre_vectorized!

    INPUT:  2d numpy array - W (Article-Topic matrix), list - article_ids,
            dict OR array - topic_relevance
    OUTPUT: list - (id, relevance) tuples
    '''
    if type(topic_relevance) is dict:
        topic_relevance_vector = np.array([v[1] for k, v in
                                           topic_relevance.iteritems()])
        article_relevance = W.dot(topic_relevance_vector.T)
    else:
        article_relevance = W.dot(topic_relevance.T)
    return zip(article_ids, article_relevance)


def final_topic_pipeline(table, query, article_relevance, relevance_threshold,
                         max_features=50000, ngram_range=(1, 3), max_df=.8,
                         n_topics=20, n_top_words=30):
    '''
    Filters irrelevant documents from the query using article_relevance
        and fits TF-IDF and NMF to form a final topic model. Prints the
        final topics out for naming (and reweighting, if necessary).

    INPUT:  mongo-collection - table, dict - mongo query,
            list - article_relevance (_id, relevance tuples)
            int - max_features, tuple - ngram_range, float - max_df,
            int - n_topics, int - n_top_words
    OUTPUT: vectorizer object - vec, 2d numpy array - H (Topic-Term matrix),
            list - topic_dicts (important terms for each topic)
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
    topic_dicts = topic_parse(vec, H, n_top_words)
    print_topics(topic_dicts)
    return vec, H, topic_dicts


def print_topics(topic_dicts):
    '''
    Prints the most important terms from each NMF-produced topic.

    INPUT:  list - topic_dicts
    OUTPUT: None
    '''
    for i, topic in enumerate(topic_dicts):
        l = sorted(topic.items(), key=lambda x: x[1])[::-1]
        print "Topic #" + str(i)
        for item in l:
            print '  ', item[1], '  ', item[0]
        print '\n'


def concise_topics(topic_dicts, n=10):
    '''
    Finds the best n terms of each topic.
    Designed for the D3 viz.

    INPUT:  list - topic_dicts, int - number of terms
    OUTPUT: list - list of terms for each topic
    '''
    concise = [None] * len(topic_dicts)
    for i, td in enumerate(topic_dicts):
        L = sorted(td.items(), key=lambda x: x[1])[:-1-n:-1]
        concise[i] = [item[0] for item in L]
    return concise


def concise_topics_named(concise, topic_list, json_filename):
    '''
    Filters the concise topics using topic_list, produces a JSON file
        suitable for the visualization.

    INPUT:  list - top terms per topic, list - topic names and weights,
            string - filename
    OUTPUT: None
    '''
    topic_filter = np.array([bool(t[1]) for t in topic_list])
    topic_names = [t[0] for t in topic_list if t[1] == 1]
    concise = np.array(concise)[topic_filter]

    d = {}
    for i, name in enumerate(topic_names):
        d[name] = ', '.join(list(concise[i]))

    json.dump(d, open(json_filename, 'w'))


def human_topic_analysis(topic_dicts):
    '''
    Presents topics one at a time, prompting the user for a name/description
        and a keep-or-discard boolean. Enter Q to quit at any time.

    INPUT:  list - topic_dicts
    OUTPUT: list - topic names and classifications
    '''
    output = [None] * len(topic_dicts)
    for i, topic in enumerate(topic_dicts):
        # print topics
        l = sorted(topic.items(), key=lambda x: x[1])[::-1]
        print "Topic #" + str(i)
        for item in l:
            print '  ', item[1], '  ', item[0]
        print '\n'
        # get name and classification
        name = raw_input("Name this topic: ")
        keep = int(raw_input("Keep? (0 or 1): "))
        if name == 'Q':
            return output
        # push to list
        output[i] = (name, keep)
    return output
