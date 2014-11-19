# Never Forget: Modeling the Topics of September 11 from 2001 to the Present

### Dan Morris, Zipfian Academy, 11/3/14 - 11/20/14

## Overview
This project is inspired by the [Timescape](http://www.fastcodesign.com/3030603/new-museum-uses-algorithms-to-visualize-how-9-11-still-shapes-the-world) exhibit in the 9/11 Memorial Museum. I used the tools and techniques of data science to investigate news topics that emerged from the events of September 11 and see how they have progressed in the years since. I used the results of my analysis to build an [interactive visualization](http://djsensei.github.io/911/) to allow anyone to explore these topics and find related articles.

## Dataset
My dataset consists of New York Times articles from 1990 to the present day. Using their [article search API](http://developer.nytimes.com/docs/read/article_search_api_v2) I scraped tens of thousands of articles related to the World Trade Center, the 9/11 attacks, and the clear effects.

### Dataset Queries
1. 'World Trade Center': 19900101 > 20141031
2. 'terrorist,terrorism,terror': 19900101 > 20141031
3. 'sept+11,september+11': 20010911 > 20141031
4. 'Qaeda': 20010911 > 20141031
5. 'Osama bin Laden': 20010911 > 20141031
6. 'homeland+security': 20010911 > 20141031
7. 'guantanamo': 20010911 > 20141031
8. 'patriot+act': 20010911 > 20141031

### Dataset Scope
The set consists of _____ articles

## Topic Modeling
The primary topics are extracted from the subset of articles published between 9/11/2001 and 3/31/2003, the time during which the literal and metaphorical dust settled. I built a clean-tokenize-TFIDF-NMF pipeline to extract the primary topics from this corpus:
1. Clean - Remove punctuation, symbols, and stopwords
2. Tokenize - Convert the cleaned string of words into a list of separate n-grams (1, 2, and 3-grams, in this case)
3. TFIDF - Compile a vocabulary of all n-grams in the corpus, use it to build a Document-Term feature matrix ('X') from the most important terms
4. NMF - Split the Document-Term matrix into two matrices ('W', 'H') whose product best approximates X. W represents Document-Topic similarity, and H represents Topic-Term similarity.

### Topic Modeling Details and Parameters
My final model used 100,000 features (terms) and 200 topics


### Stage One - Article Relevance
I run the entire corpus for the specified dates through the pipeline. Using the Topic-Term matrix H from NMF and the vocabulary of my TFIDF vectorizer, I compile the most important terms for each topic. Using my knowledge of the subject domain, I manually weight each topic's relevance to the 9/11 attacks. These weights form a vector which I multiply through the Document-Topic matrix W to determine the estimated relevance of each article. By inspection of articles at various points on the relevance spectrum, I choose a threshold and exclude all documents below that relevance.

### Stage Two - Final Topic Model
Using the article relevance data from my first stage, I run the corpus through the pipeline again, this time excluding documents whose relevance was below the threshold. The topics that emerge are inspected again to confirm relevance; upon confirmation, the TFIDF vectorizer and the H matrix from NMF are stored as the final topic model to classify future documents.

## Visualization
The topic model is visualized interactively at http://djsensei.github.io/911. I built the page from scratch in D3.js alongside the usual html and css. Users may select any combination of topics, compare their relative frequencies, and find specific articles relevant to each topic.

## Toolkit + Credits
1. [New York Times Article API](http://developer.nytimes.com/docs/read/article_search_api_v2) - Not only is this an invaluable and easy-to-use tool, I received a very quick and positive response from their support when I emailed regarding my potentially heavy use of the API over the timespan of the project.
2. [MongoDB](http://www.mongodb.org/) - Chosen because my database operations involve more dumping documents in and pulling documents out than creating complex queries.
  * [pymongo](https://github.com/mongodb/mongo-python-driver) - A python driver for MongoDB
3. [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/) - A python web-scraping library. It makes it much easier to pull out particular elements from a complex webpage.
4. [Natural Language Toolkit](http://www.nltk.org/) - Provides support for natural language processing: stopwords lists, word tokenizers, and more!
5. [scikit-learn](http://scikit-learn.org/stable/) - The granddaddy of python machine learning libraries. Indispensable.
6. [D3.js](http://d3js.org/) - "Data-Driven Documents", a javascript toolkit enabling powerful and interactive data visualizations.

## Glossary of Fancy Terms
* NMF - [Non-Negative Matrix Factorization](http://en.wikipedia.org/wiki/Non-negative_matrix_factorization)
* TFIDF - [Term Frequency - Inverse Document Frequency](http://en.wikipedia.org/wiki/Tf%E2%80%93idf)
