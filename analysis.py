'''
Topic Analysis functionality for the Always Remember project.

Dan Morris 11/3/14 - 11/20/14
'''
import pickle
import numpy as np
import pandas as pd
from mongo_stuff import just_clean_text
from collections import Counter
import simplejson as json


class TopicAnalyzer(object):
    '''
    Loads the vectorizer and H matrix necessary for document topic analysis.
    Performs large-scale analysis on the corpus.

    INPUT:  filelike - vec_file vectorizer, filelike - H topic-term matrix,
            np array - topic_filter booleans
    '''
    def __init__(self, vec_file, H_file, topic_filter=None):
        self.vectorizer = pickle.load(open(vec_file))
        self.topic_filter = topic_filter
        H = pickle.load(open(H_file))
        if topic_filter is not None:
            self.H = H[topic_filter]
        else:
            self.H = H
        self.num_topics = self.H.shape[0]


    def topic_freq_by_date_range(self, table, start_date, end_date,
                                 n_articles=1, topic_freq_threshold=.1):
        '''
        Get topic frequencies for all records in a date range. Also returns
            the highest-matching document(s) if that topic's relative
            frequency is above the topic_freq_threshold.

        INPUT:  mongo-collection - table, string - start_date,
                string - end_date, int - n_articles,
                float - topic_freq_threshold
        OUTPUT: list - (topic index, topic frequency, example
                article(s)) tuples
        '''
        q = {'pub_date': {'$gte': start_date, '$lte': end_date}}
        docs = just_clean_text(table, q)
        article_ids = np.array([d[0] for d in docs])
        X = self.vectorizer.transform([d[1] for d in docs])
        doc_topic_freqs = X.dot(self.H.T)
        total_topic_freqs = _normalize_frequencies(doc_topic_freqs.sum(axis=0))
        output = [None] * self.num_topics
        for t in range(self.num_topics):
            if total_topic_freqs[t] > topic_freq_threshold:
                tops = np.argsort(doc_topic_freqs[:, t])[::-1][:n_articles]
                output[t] = (t, total_topic_freqs[t], article_ids[tops])
            else:
                output[t] = (t, total_topic_freqs[t], None)
        return output

    def topic_count_by_date_range(self, table, start_date, end_date,
                                  doc_topic_threshold=.1,
                                  only_best_match=True):
        '''
        Returns a count of articles that match each topic above a certain
            threshold of similarity. More granular and human-interpretable
            than topic_freq_by_date_range. If only_best_match: counts
            articles for which that topic is the best match. Else: counts
            any article above that threshold per topic.

        INPUT:  mongo-collection - table, string - start_date,
                string - end_date, float - doc_topic_threshold,
                bool - only_best_match
        OUTPUT: np array - count of matching articles per topic
        '''
        q = {'pub_date': {'$gte': start_date, '$lte': end_date}}
        docs = just_clean_text(table, q)
        article_ids = np.array([d[0] for d in docs])
        texts = [d[1] for d in docs]
        article_lengths = _get_article_lengths(texts)
        X = self.vectorizer.transform(texts)
        doc_topic_freqs = X.dot(self.H.T) / article_lengths
        if only_best_match:
            best_matches = Counter(doc_topic_freqs.argmax(axis=1))
            return np.array([best_matches[i] for i in range(self.num_topics)])
        matches = doc_topic_freqs > doc_topic_threshold
        return matches.sum(axis=0)

    def current_events_analysis(self, table, n_days=7):
        '''
        Finds just articles from the last n_days for special analysis/output
        '''
        #TODO
        pass

    def empire_plot_counts(self, table, start_date='2001-10',
                           end_date='2014-11', verbose=False, **kwargs):
        '''
        Gets topic frequencies for every month in range. Output designed
            to build a stacked area chart.

        INPUT:  mongo-collection - table, string - start_date,
                string - end_date, bool - verbose,
                **kwargs for topic_freq_by_date_range
        OUTPUT: dict - freq_table of topic counts keyed by year-month
        '''
        # build date list
        dates = [start_date]
        while dates[-1] != _next_month(end_date):
            dates.append(_next_month(dates[-1]))
        freq_table = {d: [0] * self.num_topics for d in dates}
        for d in range(len(dates) - 1):
            if verbose:
                print 'getting frequencies for ', dates[d]
            freq_table[dates[d]] = self.topic_count_by_date_range(table,
                    dates[d], dates[d+1], **kwargs)
        return freq_table

    def bake_empire_csv(self, freq_table, csv_file, topic_names=None):
        '''
        Creates a CSV from the empire_plot_counts output. Easy to plug
            into D3 viz!

        INPUT:  dict - freq_table, filepath - csv_file, list - topic_names
        OUTPUT: None
        '''
        df = pd.DataFrame.from_dict(data=freq_table, orient='index').sort()
        #TODO: bake in topic names!
        df.to_csv(open(csv_file, 'w'), index_label='date')

    def store_topic_weights(self, table, model_name, normalize='linear',
                            min_doc_length=None, verbose=False):
        '''
        Calculates topic weights for each record in the table, storing them
            back into the record for easy future access. Normalize takes
            word count into account:
                'linear' - divide by word count
                'sqrt' - divide by sqrt of word count
                'none' - don't normalize

        INPUT:  mongo-collection - table, string - model_name,
                string - normalizing rule, boolean - verbose
        OUTPUT: None
        '''
        query = {'clean_text': {'$exists': True, '$ne': ''},
                 model_name: {'$exists': False}}
        cursor = table.find(query)
        i = 0
        for record in cursor:
            if verbose:
                i += 1
                if i % 500 == 0:
                    print 'updating topics for record ', i
            # push through model to get weights
            doc = record['clean_text']
            L = len(doc.split())
            if min_doc_length is not None and L < min_doc_length:
                continue
            x = self.vectorizer.transform([doc])
            dtf = x.dot(self.H.T)

            # normalize
            if normalize == 'linear':
                dtf /= L
            elif normalize == 'sqrt':
                dtf /= np.sqrt(L)

            # store weights
            table.update({'_id': record['_id']},
                         {'$set': {model_name: list(dtf[0])}})


def smooth_time_series(table, model_name, topic_names, output_csv,
                       ranked=True, rank_number=3, topic_threshold=.001,
                       month_interval=3, normalize=False):
    '''
    Time-series topic analysis; counts articles per topic-month which either:
            1) are in the n highest-ranked topics for an article
            2) exceed the given threshold
    Computes a rolling mean of some number of months, and produces a CSV
        which can be plugged into the D3 front-end for visualizing these
        trends over time.
    Normalize divides each time-series by the total number of articles per
        month to get relative frequency rather than count.

    INPUT:  mongo-collection - table, string - model_name, list - topic_names,
            string - output_csv, bool - ranked, int - rank_number,
            float - topic_threshold, int - month_interval, bool - normalize
    OUTPUT: None
    '''
    startmonth = 10 - month_interval
    query = {model_name: {'$exists':True},
             'pub_date': {'$gt': '2001-0' + str(startmonth)},
             'type_of_material':'News'}
    n = table.find(query).count()
    num_topics = len(table.find_one(query)[model_name])
    cursor = table.find(query)

    ids = [None] * n
    pubdates = [None] * n
    weights = np.zeros((n, num_topics))
    for i, record in enumerate(cursor):
        ids[i] = record['_id']
        pubdates[i] = record['pub_date'][:10]
        weights[i] = record[model_name]

    if ranked:
        tops = np.argsort(weights, axis=1)[:,-rank_number:]
        bw = np.zeros(weights.shape)
        for i, row in enumerate(tops):
            for j in row:
                bw[i, j] = 1
        bdf = pd.DataFrame(bw, index=pd.DatetimeIndex(pubdates))
    else:
        bdf = pd.DataFrame(weights > topic_threshold,
                           index=pd.DatetimeIndex(pubdates))

    bts = [None] * num_topics
    offset = pd.offsets.Week(month_interval * 2)

    if normalize:
        # determine articles per month for scaling
        all_articles_ts = pd.TimeSeries(1, pd.DatetimeIndex(sorted(pubdates)))
        abm = pd.rolling_mean(all_articles_ts.resample('M', how='count'),
                              month_interval)
        for i in range(num_topics):
            bts[i] = pd.rolling_mean(pd.TimeSeries(data=bdf[i],
                    index=bdf.index).resample('M', how='sum'),
                    month_interval) / abm
            bts[i].index = bts[i].index - offset
    else:
        for i in range(num_topics):
            bts[i] = pd.rolling_mean(pd.TimeSeries(data=bdf[i],
                    index=bdf.index).resample('M', how='sum'),
                    month_interval)
            bts[i].index = bts[i].index - offset

    outputdf = pd.concat([s for s in bts], axis=1).fillna(0)
    outputdf.columns = topic_names
    outputdf.to_csv(output_csv, index_label='date')


def get_best_articles_overall(table, model_name, topic_names,
                              start_date='2001-09', end_date='2014-11',
                              top_count=25):
    '''
    Finds the highest-weighed articles for each topic using a specified
        model. Returns a dict for further processing.

    INPUT:  mongo-collection - table, string - model_name,
            list - topic_names, string - start_date, string - end_date,
            int - top_count
    OUTPUT: dict - lists of article ids keyed by topic
    '''
    query = {model_name: {'$exists':True}, 'type_of_material':'News',
             'pub_date': {'$gt': start_date, '$lt': end_date}}
    num_topics = len(topic_names)
    N = table.find(query).count()

    bests = {}
    article_ids = [None] * N
    article_weights = np.zeros((N, num_topics))
    cursor = table.find(query)
    for i, record in enumerate(cursor):
        article_ids[i] = record['_id']
        article_weights[i] = record[model_name]
    article_ids = np.array(article_ids)

    for i, topic in enumerate(topic_names):
        best_ids = np.argsort(article_weights[:, i])[:-1-top_count:-1]
        bests[topic] = article_ids[best_ids]

    return bests


def compile_overall_best_article_json(table, model_name, best_articles,
                                      topic_names, outputfile):
    '''
    Takes best_articles dict from get_best_articles_overall, gets extra
        article information from the table, and creates a JSON file that
        the D3 front-end can use to display tooltip articles.

    INPUT:  mongo-collection - table, string - model_name,
            dict - best_articles, list - topic_names, string - outputfile
    OUTPUT: None
    '''
    num_topics = len(topic_names)
    topic_dict = {name:[] for name in topic_names}
    for topic, articles in best_articles.iteritems():
        for i, a in enumerate(articles):
            record = table.find_one({'_id': a})
            d = {'pub_date': record['pub_date'][:10],
                 'lead_paragraph': record['lead_paragraph'],
                 'headline': record['headline'],
                 'web_url': record['web_url']}
            topic_dict[topic].append(d)

    json.dump(topic_dict, open(outputfile, 'w'))


def get_best_articles_per_month(table, model_name, start_date='2001-09',
                                end_date='2014-11', verbose=False):
    '''
    Finds the highest-weighed article every month for each topic,
        using a specified model. Returns a dict for further processing.

    INPUT:  mongo-collection - table, string - model_name,
            string - start_date, string - end_date, bool - verbose
    OUTPUT: dict - best_articles keyed by month
    '''
    query = {model_name: {'$exists':True}, 'type_of_material':'News'}
    num_topics = len(table.find_one(query)[model_name])

    dates = [start_date]
    while dates[-1] != _next_month(end_date):
        dates.append(_next_month(dates[-1]))
    best_articles = {}
    for d in range(len(dates) - 1):
        if verbose:
            print 'selecting best articles for ', dates[d]
        best_this_month = [(None, 0.0)] * num_topics
        query['pub_date'] = {'$gte': dates[d], '$lt': dates[d + 1]}
        cursor = table.find(query)
        for record in cursor:
            w = record[model_name]
            for i, v in enumerate(w):
                if v > best_this_month[i][1]:
                    best_this_month[i] = (record['_id'], v)
        best_articles[dates[d]] = best_this_month

    return best_articles


def compile_best_article_json(table, model_name, best_articles, topic_list,
                              outputfile):
    '''
    Takes best_articles dict from get_best_articles_per_month, gets extra
        article information from the table, and creates a JSON file that
        the D3 front-end can use to display tooltip articles.

    INPUT:  mongo-collection - table, string - model_name,
            dict - best_articles, list - topic_list, string - outputfile
    OUTPUT: None
    '''
    num_topics = len(topic_list)
    topic_dict = {i:[] for i in range(num_topics)}
    for month, topics in best_articles.iteritems():
        for i, t in enumerate(topics):
            record = table.find_one({'_id': t[0]})
            d = {'pub_date': record['pub_date'][:10],
                 'lead_paragraph': record['lead_paragraph'],
                 'headline': record['headline'],
                 'web_url': record['web_url'],
                 'weight': t[1],
                 '_id': t[0],
                 'weights_sum': sum(record[model_name])}
            topic_dict[i].append(d)
    for i, t in enumerate(topic_list):
        topic_dict[t] = topic_dict.pop(i)

    json.dump(topic_dict, open(outputfile, 'w'))


def filter_best_article_json(filename=None, jsond=None, threshold=.001):
    '''
    Filters out articles below the threshold. Input either a filename for
        a JSON file or the json dictionary itself.

    INPUT:  string - filename, dict - jsond, float - threshold
    OUTPUT: dict - filtered json
    '''
    if filename is not None:
        baj = json.load(open(filename))
    else:
        baj = jsond
    filtered_baj = {k: [] for k in baj.keys()}
    for k, L in baj.iteritems():
        high_enough = []
        for article in L:
            if article['weight'] >= threshold:
                high_enough.append(article)
        filtered_baj[k] = high_enough
    return filtered_baj


def _normalize_frequencies(f):
    '''
    Normalizes and returns array f so that it sums to 1.
    '''
    return f / sum(f)


def _get_article_lengths(docs):
    '''
    Determines the length of each document in docs for normalizing TFIDF

    INPUT:  list length n - documents
    OUTPUT: n x 1 np array - length of docs
    '''
    L = np.zeros((len(docs), 1))
    for i, d in enumerate(docs):
        L[i] = len(d.split())
    return L


def _next_month(d):
    '''
    Given a year-month string, returns a string for the next month.

    INPUT:  string - d ('YYYY-MM')
    OUTPUT: string - d ('YYYY-MM')
    '''
    y = int(d[:4])
    m = int(d[-2:])
    if m == 12:
        return str(y + 1) + '-01'
    elif m < 9:
        return str(y) + '-0' + str(m + 1)
    else:
        return str(y) + '-' + str(m + 1)
