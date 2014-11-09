'''
Current Events functionality. Scrapes recent articles, compares them to the
    existing topic model, etc.
'''
import datetime as dt
import nyt_scrape as nyt
import nlp


def get_current_events(table, n_days=7):
    '''
    Scrapes all articles from recent days and pushes them through the
        cleaning pipeline, storing all results in table.

    INPUT:  mongo-collection - table, int - n_days
    OUTPUT: None
    '''
    print 'building query'
    today = dt.datetime.today()
    end_date = nyt._date_string(today.year, today.month, today.day)
    bday = today - dt.timedelta(n_days)
    begin_date = nyt._date_string(bday.year, bday.month, bday.day)
    param_dict = {'begin_date': begin_date, 'end_date': end_date}
    url = nyt._query_url(param_dict=param_dict)

    print 'querying API'
    records, _ = nyt.many_queries(None, None, 10000, url)

    print 'loading DB with new records'
    nyt.load_mongo(table, records)

    print 'scraping full texts'
    nyt.load_full_texts_from_docs(table, records)

    print 'cleaning new docs'
    nlp.clean_these_docs(table, records)
