'''
Specific scraping jobs for the nyt scraper. Designed to run a long time on their own.
'''

import nyt_scrape as nyt
from pymongo import MongoClient

if __name__=='__main__':
    db = nyt.mongo_connection()
    table = db.firstyear

    q = 'World Trade Center'
    present_date = '20030101'
    end_date = '20031231'
    param_dict = {'begin_date': present_date,
                  'end_date': '20021031',
                  'sort': 'oldest'}
    while present_date < '20021031':
        print 'loading articles from ', present_date
        docs, present_date = nyt.many_queries(q, param_dict)
        print 'pushing articles into mongo'
        nyt.load_mongo(table, docs)
        print 'scraping full texts of new documents'
        nyt.load_full_texts_from_docs(table, docs, verbose=True)
        param_dict['begin_date'] = present_date

    print 'ALL DONE! YOU DID IT!'
