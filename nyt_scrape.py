'''
NYT scraping for Timescape project

parameter guidelines:
begin_date: yyyymmdd
end_date: yyyymmdd
page: int (10 results per page)

notes: make sure mongod is up and running. use `sudo mongod` in terminal
'''
import requests
from pymongo import MongoClient
from bs4 import BeautifulSoup
import simplejson as json
from time import sleep

BASE_URL = 'http://api.nytimes.com/svc/search/v2/articlesearch.json?'
with open('nytapi.txt') as f:
    API_KEY = f.read().strip('\n')

# not used yet, but could be. These url snippets always fail to scrape.
URLS_TO_IGNORE = set(['http://www.nytimes.com/video', 'http://www.legacy.com',
                      'http://www.nytimes.com/slideshow',
                      'http://cooking.nytimes.com/recipes',
                      'http://www.nytimes.com/interactive'])


def mongo_connection():
    '''
    Creates a connection to the relevant mongodb database.

    INPUT:  None
    OUTPUT: mongo-connection - to db 'neverforget'
    '''
    client = MongoClient('mongodb://localhost:27017/')
    db = client.neverforget
    return db


def _query_url(q='', param_dict={}):
    '''
    Creates a query url for the NYT API. Leave q empty to get all articles
        that match param_dict.

    INPUT:  string - q (the query), dict - param_dict (any input parameters
            such as begin_date, end_date, sort, etc.)
    OUTPUT: string - url
    '''
    url = BASE_URL
    if q:
        url += 'q=' + q + '&'
    for p, v in param_dict.iteritems():
        url += p + '=' + v + '&'
    url += 'api-key=' + API_KEY
    return url


def single_query(url):
    '''
    Makes a request to the NYT API and returns document metadata.

    INPUT:  string - url
    OUTPUT: list - document records (JSON dicts)
    '''
    response = requests.get(url)
    if response.status_code != 200:
        print 'scrape error: status code', response.status_code
        return None
    d = response.json()
    docs = d['response']['docs']  # document records
    return docs


def count_query(url):
    '''
    Makes a request to the NYT API and returns the count of docs that
        match the query.

    INPUT:  string - url
    OUTPUT: int - number of hits OR None - request failed
    '''
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['response']['meta']['hits']
    print 'Request Failed', response_status_code
    return None


def date_process(pub_date):
    '''
    Transforms pub_date string into the format that the NYT API likes.

    INPUT:  string - timestamp
    OUTPUT: string - date
    '''
    return ''.join(pub_date.split('T')[0].split('-'))


def many_queries(q=None, param_dict=None, max_pages=10, url=None):
    '''
    Queries the NYT API repeatedly to accumulate many documents.
    Designed to scrape as many results from the given query as possible
        at 10 results per page.

    INPUT:  string - q, dict - param_dict, int - max_pages
            OR (if your API url is already built)
            string - url, int - max_pages
    OUTPUT: list - document record dicts, string - date of last result
    '''
    if not url:
        url = _query_url(q, param_dict)
    response = requests.get(url)
    d = response.json()
    hits = d['response']['meta']['hits']  # number of results
    print 'Found ', hits, ' hits to the query'
    n = hits / 10
    docs = d['response']['docs']
    present_date = date_process(docs[-1]['pub_date'])
    for p in range(1, min(max_pages, n+1)):
        # add the page number to the query, make it again
        new_url = url.split('api-key')
        new_url[0] += 'page=' + str(p) + '&'
        new_url = 'api-key'.join(new_url)
        try:  # don't lose the docs we already have if if borks
            new_docs = single_query(new_url)
            if new_docs is not None:
                docs += new_docs
                present_date = date_process(new_docs[-1]['pub_date'])
            else:
                # reset the beginning of the date
                print 'Last successful date: ', present_date
                break
        except:
            print 'Broken.'
            break
    return docs, present_date


def load_mongo(table, docs):
    '''
    Adds new documents to the database.

    INPUT:  mongo-collection - table, list - document records
    OUTPUT: set - ids of docs already in the table
    '''
    # load new documents into mongo table, checking for existence using _id
    ignore_ids = set()
    for d in docs:
        if table.find_one({'web_url': d['web_url']}) is None:
            d['full_text'] = ''
            table.update({'_id': d['_id']}, d, upsert=True)
        else:
            ignore_ids.add(d['_id'])
    return ignore_ids

def get_full_text(web_url):
    '''
    Scrapes the full article text from a single web_url. Designed to
        handle a variety of html article styles that the NYT website
        has used over time.

    INPUT:  string - web_url
    OUTPUT: string - full article text (or '' if no article exists)
    '''
    try:
        r = requests.get(web_url)
        if r.status_code != 200:
            print 'error: status code ', r.status_code
            return ''
        s = BeautifulSoup(r.text, 'html.parser')
    except:
        print 'requests error with url: ', web_url
        return ''

    # Deal with the different formattings of articles in HTML
    if s.find('p', {'itemprop': 'articleBody'}) is not None:
        paragraphs = s.findAll('p', {'itemprop': 'articleBody'})
        story = ' '.join([p.text for p in paragraphs])
    elif s.find('nyt_text'):
        story = s.find('nyt_text').text
    elif s.find('div', {'id': 'mod-a-body-first-para'}):
        story = s.find('div', {'id': 'mod-a-body-first-para'}).text
        story += s.find('div', {'id': 'mod-a-body-after-first-para'}).text
    else:
        if s.find('p', {'class': 'story-body-text'}) is not None:
            paragraphs = s.findAll('p', {'class': 'story-body-text'})
            story = ' '.join([p.text for p in paragraphs])
        else:
            story = ''

    if story == '':
        print 'bad scrape. web_url: ', web_url
    return story


def load_full_texts(table, verbose=False):
    '''
    Attempts to scrape full article text for every article in the table
        which currently lacks it. Use of load_full_texts_from_docs
        in real time during a scrape is preferred.

    INPUT:  mongo-collection - table, bool - verbose
    OUTPUT: None
    '''
    for record in table.find({'document_type': 'article',
                              'full_text': '',
                              'type_of_material': 'News',
                              'failed_scrape': {'$exists':False}}):
        story = get_full_text(record['web_url'])
        if verbose:
            print story[:100]
        if story != '':
            table.update({'_id': record['_id']},
                         {'$set': {'full_text': story}},
                         upsert=True)
        else:
            table.update({'_id': record['_id']},
                         {'$set': {'failed_scrape': True}})


def load_full_texts_from_docs(table, docs, verbose=False):
    '''
    Attempts to scrape full article texts for every article in the
        given list of docs. Generally used immediately after the API
        returns these docs.

    INPUT:  mongo-collection - table, list - docs, bool - verbose
    OUTPUT: None
    '''
    for i, d in enumerate(docs):
        if table.find_one({'web_url': d['web_url']}) is not None:
            story = get_full_text(d['web_url'])
            if verbose and i % 50 == 0:
                print 'doc ', i, ': ', story[:100]
            if story != '':
                table.update({'_id': d['_id']},
                             {'$set': {'full_text': story}},
                             upsert=True)
            else:
                table.update({'_id': d['_id']},
                             {'$set': {'failed_scrape': True}})


def nyt_article_counts_by_day(ymd_start='20130101', ymd_end='20131231'):
    '''
    Pings the NYT API to count the total number of articles by day.

    INPUT:  string - start date, string - end date
    OUTPUT: dict - article counts keyed by day
    '''
    counts = {}
    for year in range(int(ymd_start[:4]), int(ymd_end[:4]) + 1):
        for month in range(1, 13):
            for day in range(1, 32):
                ds = _date_string(year, month, day)
                if ds <= ymd_start:
                    continue
                if ds > ymd_end:
                    return counts
                url = _query_url(param_dict={'begin_date': ds,
                                             'end_date': ds})
                try:
                    n = count_query(url)
                    if n is not None:
                        counts[ds] = n
                    else:
                        print 'failed request. last attempt: ', ds
                        return counts
                except:
                    pass
                # sleep(.1) # tweak this to avoid rate limits?
    return counts


def nyt_article_counts_json(counts, filename):
    '''
    Dumps daily article counts from nyt_article_counts_by_day into a
        JSON file for future reference.

    INPUT:  dict - counts, string - filename
    OUTPUT: None
    '''
    with open(filename, 'w') as wf:
        json.dump(counts, wf)


def _date_string(y, m, d):
    '''
    Converts numeric year, month, and day into a date string compatible
        with the NYT API.
    TODO: prevent it from returning days that don't
        exist (like February 31).

    INPUT:  int - year, int - month, int - day
    OUTPUT: string - date
    '''
    s = str(y)
    if m < 10:
        s += '0' + str(m)
    else:
        s += str(m)
    if d < 10:
        s += '0' + str(d)
    else:
        s += str(d)
    return s


def _invert_date_string(s):
    '''
    Converts a date string into year, month, and day integers. The inverse
        of _date_string.

    INPUT:  string - date
    OUTPUT: tuple - int year, int month, int day
    '''
    y = int(s[:4])
    m = int(s[4:6])
    d = int(s[6:])
    return (y, m, d)
