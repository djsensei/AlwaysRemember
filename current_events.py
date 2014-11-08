'''
Current Events functionality. Scrapes recent articles, compares them to the
    existing topic model, etc.
'''
import datetime as dt
from nyt_scrape import _date_string, _noquery_url, many_queries, \
                       load_full_texts_from_docs, load_mongo
from nlp import clean_these_docs

def get_current_events(table, n_days=7):
    '''
    Scrapes all articles from the last n_days days, pushes them through the
        cleaning pipeline into table.
    '''
    print 'building query'
    today = dt.datetime.today()
    end_date = _date_string(today.year, today.month, today.day)
    bday = today - dt.timedelta(n_days)
    begin_date = _date_string(bday.year, bday.month, bday.day)
    param_dict = {'begin_date': begin_date, 'end_date': end_date}
    url = _noquery_url(param_dict)

    print 'querying API'
    records, _ = many_queries(None, None, 10000, url)

    print 'loading DB with new records'
    load_mongo(table, records)

    print 'scraping full texts'
    load_full_texts_from_docs(table, records)

    print 'cleaning new docs'
    clean_these_docs(table, records)
