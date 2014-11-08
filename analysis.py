'''
Using the pre-compiled topic model, determine topic frequencies by date ranges
'''
import pickle
import numpy as np
from mongo_stuff import just_clean_text

class TopicAnalyzer(object):
    def __init__(self, vec_file, H_file):
        self.vectorizer = pickle.load(open(vec_file))
        self.H = pickle.load(open(H_file))
        self.num_topics = self.H.shape[0]

    def topic_freq_by_date_range(self, table, start_date, end_date,
                                 n_articles=1, topic_freq_threshold=.1):
        '''
        Query table for docs in date range, run through topic model, return
            a list of tuples:
            (topic_id, frequency, list of n article ids)
        Will only return article IDs for a topic if that topic's share exceeds
            the topic_freq_threshold.
        '''
        q = {'pub_date': {'$gte': start_date, '$lte': end_date}}
        docs = just_clean_text(table, q)
        article_ids = np.array([d[0] for d in docs])
        X = self.vectorizer.transform([d[1] for d in docs])
        doc_topic_freqs = X.dot(self.H.T)
        total_topic_freqs = normalize_frequencies(doc_topic_freqs.sum(axis=0))
        output = [None] * self.num_topics
        for t in range(self.num_topics):
            if total_topic_freqs[t] > topic_freq_threshold:
                tops = np.argsort(doc_topic_freqs[:,t])\
                                  [::-1][:n_articles]
                output[t] = (t, total_topic_freqs[t], article_ids[tops])
            else:
                output[t] = (t, total_topic_freqs[t], None)
        return output



def normalize_frequencies(f):
    '''
    normalizes the frequencies in array f to sum to 1
    '''
    return f / sum(f)
