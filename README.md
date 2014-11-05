# Topic Analysis of News in a Post-9/11 World

### Dan Morris, Zipfian Academy, 11/3/14 - 11/21/14

## Overview
This project is inspired by the [Timescape](http://www.fastcodesign.com/3030603/new-museum-uses-algorithms-to-visualize-how-9-11-still-shapes-the-world) exhibit in the 9/11 Memorial Museum. Using a large corpus of 9/11-related documents, I extract high-level topics and explore the ways that news coverage related to those topics has changed over the years since the attacks.

## Dataset
My primary data source is articles from the New York Times. Using their API, I scraped as many articles as possible related to the World Trade Center and the 9/11 attacks.

### Dataset Scope
It is important to include articles from well before 9/11 all the way up to the present day. While the articles from the days and weeks immediately following the attacks are most important for building the set of topics that were spawned from 9/11, the articles from days, weeks, and even years before that day are important for establishing a baseline of media coverage. Once initial topics have been compiled, the articles from 2002 up to the present day form the basis for compelling analysis of how the news landscape has been changed (as well as how current events relate to those topics, even though the composition of the current events may have little to do with the exact details of the original events.)

The set consists of _____ articles, as well as information about the total number of articles published by the NYT on each day for relative frequency comparison.

## Topic Modeling
The primary topics are extracted from a set of articles published between 9/11/2001 and 12/31/2002, the time during which the literal and metaphorical dust settled. After cleaning these documents of punctuation, symbols, and stopwords, I vectorized them with TFIDF, using 1-, 2-, and 3-grams. The topics were extracted from the TFIDF feature matrix using NMF. From the topics that NMF produces and the vocabulary of my TFIDF vectorizer, I list the most important terms for each topic and use human intuition to extract a brief description of that topic which serves as its label moving forward.

## Visualization

## Toolkit + Credits
1. [New York Times Article API](http://developer.nytimes.com/docs/read/article_search_api_v2) - Not only is this an invaluable and easy-to-use tool, I received a very quick and positive response from their support when I emailed regarding my potentially heavy use of the API over the timespan of the project.
2. [MongoDB](http://www.mongodb.org/) - Chosen because my database operations involve more dumping documents in and pulling documents out than creating complex queries.
  * [pymongo](https://github.com/mongodb/mongo-python-driver) - A python driver for MongoDB
3. [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/) - A python web-scraping library. It makes it much easier to pull out particular elements from a complex webpage.
4. [Natural Language Toolkit](http://www.nltk.org/) - Provides support for natural language processing: stopwords lists, word tokenizers, and more!
5. [scikit-learn](http://scikit-learn.org/stable/) - The granddaddy of python machine learning libraries. Indispensable.

## Glossary of Fancy Terms
* NMF - [Non-Negative Matrix Factorization](http://en.wikipedia.org/wiki/Non-negative_matrix_factorization)
* TFIDF - [Term Frequency - Inverse Document Frequency](http://en.wikipedia.org/wiki/Tf%E2%80%93idf)
