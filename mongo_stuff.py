'''
Standalone functions and reports on the mongo db.
'''
from pymongo import MongoClient
from collections import Counter

def records_by_month(table, query={}):
    '''
    returns a list of (month, count) tuples
    '''
    mc = Counter()
    for record in table.find(query):
        month = record['pub_date'][:7]
        mc[month] += 1
    return mc

def just_clean_text(table, query={}):
    '''
    Queries the table and returns a list of clean text documents (id, text)
    '''
    query['clean_text'] = {'$exists': True, '$ne': ''}
    cursor = table.find(query)
    results = [(c['_id'], c['clean_text']) for c in cursor]
    return results
