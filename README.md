# Topic Analysis of News in a Post-9/11 World

### Dan Morris, Zipfian Academy, 11/3/14 - 11/21/14

## Overview
This project is inspired by the [Timescape](http://www.fastcodesign.com/3030603/new-museum-uses-algorithms-to-visualize-how-9-11-still-shapes-the-world) exhibit in the 9/11 Memorial Museum. Using a large corpus of 9/11-related documents, I extract high-level topics and explore the ways that news coverage related to those topics has changed over the years since the attacks.

## Dataset
My primary data source is articles from the New York Times. Using their API, I scraped as many articles as possible related to the World Trade Center and the 9/11 attacks.

### Dataset Scope
It is important to include articles from well before 9/11 all the way up to the present day. While the articles from the days and weeks immediately following the attacks are most important for building the set of topics that were spawned from 9/11, the articles from days, weeks, and even years before that day are important for establishing a baseline of media coverage. Once initial topics have been compiled, the articles from 2002 up to the present day form the basis for compelling analysis of how the news landscape has been changed (as well as how current events relate to those topics, even though the composition of the current events may have little to do with the exact details of the original events.)

The set consists of _____ articles, as well as information about the total number of articles published by the NYT on each day for relative frequency comparison.

### Dataset Queries
1. 'World Trade Center': 19900101 > 20141031
2. 'terrorist,terrorism,terror': 19900101 > 20141031
3. 'sept+11,september+11': 20010911 > 20141031

## Topic Modeling
The primary topics are extracted from a set of articles published between 9/11/2001 and 3/31/2003, the time during which the literal and metaphorical dust settled. I built a clean-tokenize-TFIDF-NMF pipeline to extract the primary topics from this corpus:
1. Clean - Remove punctuation, symbols, and stopwords
2. Tokenize - Convert the cleaned string of words into a list of separate n-grams (1, 2, and 3-grams, in this case)
3. TFIDF - Compile a vocabulary of all n-grams in the corpus, use it to build a Document-Term feature matrix ('X') from the most important terms
4. NMF - Split the Document-Term matrix into two matrices ('W', 'H') whose product best approximates X. W represents Document-Topic similarity, and H represents Topic-Term similarity.

### Stage One - Article Relevance
I run the entire corpus for the specified dates through the pipeline. Using the Topic-Term matrix H from NMF and the vocabulary of my TFIDF vectorizer, I compile the most important terms for each topic. Using my knowledge of the subject domain, I manually weight each topic's relevance to the 9/11 attacks. These weights form a vector which I multiply through the Document-Topic matrix W to determine the estimated relevance of each article. By inspection of articles at various points on the relevance spectrum, I choose a threshold and exclude all documents below that relevance.

### Stage Two - Final Topic Model
Using the article relevance data from my first stage, I run the corpus through the pipeline again, this time excluding documents whose relevance was below the threshold. The topics that emerge are inspected again to confirm relevance; upon confirmation, the TFIDF vectorizer and the H matrix from NMF are stored as the final topic model to classify future documents. 

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
