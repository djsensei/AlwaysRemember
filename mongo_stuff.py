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
