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

baseurl = 'http://api.nytimes.com/svc/search/v2/articlesearch.json?'
api_key = 'f5720d095a40f76fc4c1e2c4b4657e8f:15:57014703'

def mongo_connection():
    client = MongoClient('mongodb://localhost:27017/')
    db = client.neverforget
    return db

def _query_url(q, param_dict={}):
    '''
    Creates a query on the NYT API with specified parameters
    '''
    url = baseurl + 'q=' + q + '&'
    for p, v in param_dict.iteritems():
        url += p + '=' + v + '&'
    url += 'api-key=' + api_key
    return url

def _noquery_url(param_dict={}):
    '''
    Queries the NYT API without an actual query. Useful for article counts by
        date.
    '''
    url = baseurl
    for p, v in param_dict.iteritems():
        url += p + '=' + v + '&'
    url += 'api-key=' + api_key
    return url

def single_query(url):
    response = requests.get(url)
    if response.status_code != 200:
        print 'scrape error: status code', response.status_code
        return None
    d = response.json()
    docs = d['response']['docs'] # document records
    return docs

def count_query(url):
    '''
    Simply counts articles by day
    '''
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['response']['meta']['hits']
    return 'Request Failed', response.status_code

def date_process(pub_date):
    '''
    Transforms "2002-12-31T00:00:00Z" into "20021231" so NYT likes it
    '''
    return ''.join(pub_date.split('T')[0].split('-'))

def many_queries(q, param_dict, max_pages=10):
    '''
    Designed to scrape as many results from the given query as possible.
    Overcomes adversity and defeats the API limits!
    '''
    url = _query_url(q, param_dict)
    response = requests.get(url)
    d = response.json()
    hits = d['response']['meta']['hits'] # number of results
    print 'Found ', hits, ' hits to the query'
    n = hits / 10
    docs = d['response']['docs']
    present_date = date_process(docs[-1]['pub_date'])
    for p in range(1, min(max_pages, n+1)):
        # add the page number to the query, make it again
        new_url = url.split('api-key')
        new_url[0] += 'page=' + str(p) + '&'
        new_url = 'api-key'.join(new_url)
        try: # don't lose the docs we already have if if borks
            new_docs = single_query(new_url)
            if new_docs != None:
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
    # load new documents into mongo table, checking for existence using _id
    for d in docs:
        d['full_text'] = ''
        table.update({'_id': d['_id']}, d, upsert=True)

def get_full_text(web_url):
    '''
    Scrapes article text from a single web_url, returns the article as string.
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
    if s.find('nyt_text'):
        story = s.find('nyt_text').text
    elif s.find('div', {'id':'mod-a-body-first-para'}):
        story = s.find('div', {'id':'mod-a-body-first-para'}).text
        story += s.find('div', {'id':'mod-a-body-after-first-para'}).text
    else:
        if s.find('p', {'class':'story-body-text'}) != None:
            paragraphs = s.findAll('p', {'class':'story-body-text'})
            story = ' '.join([p.text for p in paragraphs])
        elif s.find('p', {'itemprop':'articleBody'}) != None:
            paragraphs = s.findAll('p', {'itemprop':'articleBody'})
            story = ' '.join([p.text for p in paragraphs])
        else:
            story = ''

    if story == '':
        print 'bad scrape. web_url: ', web_url
    return story

def load_full_texts(table, verbose=False):
    '''
    Iterates through table, checking for existence of a full_text field in each
        document. If that field doesn't exist, we try to scrape it and add it
        in! Runs until some failure.
    '''
    for record in table.find({'document_type':'article', 'full_text':''}):
        story = get_full_text(record['web_url'])
        if verbose:
            print story[:100]
        table.update({'web_url': record['web_url']},
                     {'$set': {'full_text': story}},
                     upsert=True)

def load_full_texts_from_docs(table, docs, verbose=False):
    '''
    Only looks at new documents to avoid going through the whole table each
        scrape-iteration.
    '''
    for i, d in enumerate(docs):
        if table.find_one({'web_url':d['web_url']}) != None:
            story = get_full_text(d['web_url'])
            if verbose and i%50==0:
                print 'doc ', i, ': ', story[:100]
            table.update({'web_url': d['web_url']},
                         {'$set': {'full_text': story}},
                         upsert=True)

def query_and_load_db(table, q, param_dict):
    '''
    Compresses the process into a single function!
    Just enter your table and your query info, sit back, and enjoy!
    '''
    docs, present_date = many_queries(q, param_dict)
    load_mongo(table, docs)
    load_full_texts(table, verbose=True)

def troubleshoot_full_text(table):
    '''
    Returns a single example of a record whose full_text == '', so I can make
        sure that the get_full_text module works for all sorts of documents.
    '''
    record = table.find_one({'full_text':''})
    r = requests.get(record['web_url'])
    s = BeautifulSoup(r.text, 'html.parser')
    return s

def nyt_article_counts_by_day(ymd_start='20130101', ymd_end='20131231'):
    '''
    Pings an empty query to the nyt API for every day from start to finish
        to determine how many total articles there were (for scaling
        proportions of articles which match a given topic).
    Returns a dict. Store as a json file!
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
                url = _noquery_url({'begin_date':ds, 'end_date':ds})
                try:
                    n = count_query(url)
                    if n != 'Request Failed':
                        counts[ds] = n
                    else:
                        print 'failed request. last attempt: ', ds
                        return counts
                except:
                    pass
                # sleep(.1) # tweak this to avoid rate limits?
    return counts

def nyt_article_counts_json(counts, filename):
    with open(filename, 'w') as wf:
        json.dump(counts, wf)

def _date_string(y, m, d):
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
    y = int(s[:4])
    m = int(s[4:6])
    d = int(s[6:])
    return (y, m, d)
