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

def single_query(url):
    response = requests.get(url)
    if response.status_code != 200:
        print 'scrape error: status code', response.status_code
        return None
    d = response.json()
    docs = d['response']['docs'] # document records
    return docs

def many_queries(url):
    response = requests.get(url)
    d = response.json()
    hits = d['response']['meta']['hits'] # number of results
    n = hits / 10
    docs = d['response']['docs']
    for p in range(1, n+1):
        # add the page number to the query, make it again
        new_url = url.split('api-key')
        new_url[0] += 'page=' + str(p) + '&'
        new_url = 'api-key'.join(new_url)
        new_docs = single_query(new_url)
        if new_docs != None:
            docs += single_query(new_url)
        else:
            break
    return docs

def load_mongo(table, docs):
    # load new documents into mongo table, checking for existence using web_url
    for d in docs:
        table.update({'web_url': d['web_url']}, d, upsert=True)

def get_full_text(web_url):
    '''
    Scrapes article text from a single web_url, returns the string
    '''
    r = requests.get(web_url)
    if r.status_code != 200:
        print 'error: status code ', r.status_code
        return None
    s = BeautifulSoup(r.text, 'html.parser')
    paragraphs = s.findAll('p', {'class':'story-body-text'})
    story = ' '.join([p.text for p in paragraphs])
    return story

def load_full_texts(table, verbose=False):
    '''
    Iterates through table, checking for existence of a full_text field in each
        document. If that field doesn't exist, we try to scrape it and add it
        in! Runs until some failure.
    '''
    for record in table.find({'document_type':'article'}):
        if record.get('full_text', None) == None:
            story = get_full_text(record['web_url'])
            if verbose:
                print story[:50]
            table.update({'web_url': record['web_url']},
                         {'$set': {'full_text': story}},
                         upsert=True)

def query_and_load_db(table, q, param_dict):
    '''
    Compresses the process into a single function!
    Just enter your table and your query info, sit back, and enjoy!
    '''
    url = _query_url(q, param_dict)
    docs = many_queries(url)
    load_mongo(table, docs)
    load_full_texts(table)
