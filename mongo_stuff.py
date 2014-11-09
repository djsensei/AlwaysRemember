'''
Standalone functions and reports on the mongo db.
'''
from pymongo import MongoClient
from collections import Counter


def records_by_month(table, query={}):
    '''
    Counts query-matching records in the table per month.

    INPUT:  mongo-collection - table, dict - query
    OUTPUT: dict - record counts keyed by year-month string
    '''
    mc = Counter()
    for record in table.find(query):
        month = record['pub_date'][:7]
        mc[month] += 1
    return mc


def just_clean_text(table, query={}):
    '''
    Gets the clean text from every query-matching record in the table.

    INPUT:  mongo-collection table, dict - query
    OUTPUT: list - clean document strings
    '''
    query['clean_text'] = {'$exists': True, '$ne': ''}
    cursor = table.find(query)
    results = [(c['_id'], c['clean_text']) for c in cursor]
    return results
