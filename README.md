# [Always Remember](http://djsensei.github.io/911): Modeling the Topics of September 11 from 2001 to the Present

### Dan Morris, Zipfian Academy, 11/3/14 - 11/20/14

## Overview
This project is inspired by the [Timescape](http://www.fastcodesign.com/3030603/new-museum-uses-algorithms-to-visualize-how-9-11-still-shapes-the-world) exhibit in the 9/11 Memorial Museum. I used the tools and techniques of data science to investigate news topics that emerged from the events of September 11 and track their newsworthiness in the years since. I used the results of my analysis to build an [interactive visualization](http://djsensei.github.io/911/) so anyone can explore these topics and find related articles.

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
The primary dataset for modeling consists of 63,747 New York Times articles. These are filtered from an even larger set of articles; for each I was able to scrape the full article text, and the text contained at least 30 words.

## Topic Modeling
The primary topics are extracted from the subset of articles published between 9/11/2001 and 3/31/2003, the time during which the literal and metaphorical dust settled. I built a clean-tokenize-TFIDF-NMF pipeline to extract the primary topics from this corpus:
1. Clean - Remove punctuation, symbols, and stopwords
2. Tokenize - Convert the cleaned string of words into a list of separate n-grams (1, 2, and 3-grams, in this case)
3. TFIDF - Compile a vocabulary of all n-grams in the corpus, use it to build a Document-Term feature matrix ('X') from the most important terms
4. NMF - Split the Document-Term matrix into two matrices ('W', 'H') whose product best approximates X. W represents Document-Topic weighting, and H represents Topic-Term weighting.

### Topic Modeling Details and Parameters
My final model used 100,000 terms/features (1-, 2-, and 3-grams) and 200 topics. To train such a large model I spun up an AWS x-large machine, which took about 6 hours to finish the job.

### Topic Filtering
Because the documents are scraped from broad query results and the NMF algorithm doesn't know anything about the documents, terms, or topics it contains, I manually inspected and named each topic that emerged from the model. Out of the 200 topics, I deemed 75 worthy of inclusion in the visualization. The others were discarded for various reasons: they were too generic/broad, too specific to individual articles, or irrelevant to the primary topic.

## Analysis
I pickled the TF-IDF and NMF models produced by the topic modeling step so that they could be used to classify any article. To determine the topic of an article, I vectorize it with the TF-IDF vectorizer and multiply it by the transposed H matrix from the NMF model (with discarded topic rows removed). The result is an array which has one element for each topic (that represents the article's relevance to that topic).

### Analysis Choices and Details
I made a few choices to increase the effectiveness of the visualization:
1. I classified each article as each of its three highest-weighted topics because I found that using a fixed threshold for classification led to unbalanced and inaccurate results.
2. I compiled the counts of relevant articles by month, but used a 4-month rolling mean to smooth out the plot without losing relevant spikes.
3. I normalized the values of each month by the total count of articles from that month in the corpus. This ensured that the months after 9/11 weren't overrepresented across almost all of the topics, but it led to some topics appearing larger in recent years.

### Example Articles
For each topic, I selected the 25 articles with the highest relevance score to that topic. The accuracy of this method is quite high (few off-topic articles appear), but the downside is that many topics have visible spikes in the plot without accompanying articles to explain what happened during that time period. These selected articles appear as dots above the plot on the visualization, and can be clicked to obtain more details and a link to the full article.

## Visualization
The topic model is visualized interactively at http://djsensei.github.io/911. I built the page from scratch using D3.js alongside the usual html and css. Users may select any combination of topics, compare their relative frequencies, see what top terms form any topic, and find specific articles relevant to each topic.

## Possible Next Steps
* Separate individual-person topics from general topics.
* Analytically determine where spikes occur in each topic and find highly-relevant articles at that time.
* Explore other subjects using the same scrape-model-analyze-visualize pipeline
* Use more robust NLP techniques (stemming or lemmatization) in pre-processing the full article texts.
* Sum topic weights for all articles rather than classifying articles as binary relevant-or-not to a given topic.

## Toolkit + Credits
1. [New York Times Article API](http://developer.nytimes.com/docs/read/article_search_api_v2) - Not only is this an invaluable and easy-to-use tool, I received a very quick and positive response from their support when I emailed regarding my potentially heavy use of the API over the timespan of the project.
2. [MongoDB](http://www.mongodb.org/) - Chosen because my database operations involve more dumping documents in and pulling documents out than creating complex queries.
  * [pymongo](https://github.com/mongodb/mongo-python-driver) - A python driver for MongoDB
3. [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/) - A python web-scraping library. It makes it much easier to pull out particular elements from a complex webpage.
4. [Natural Language Toolkit](http://www.nltk.org/) - Provides support for natural language processing: stopwords lists, word tokenizers, and more!
5. [scikit-learn](http://scikit-learn.org/stable/) - The granddaddy of python machine learning libraries. Indispensable.
6. [D3.js](http://d3js.org/) - "Data-Driven Documents", a javascript toolkit enabling powerful and interactive data visualizations.
7. [i want hue](http://tools.medialab.sciences-po.fr/iwanthue/) - Colors for data scientists! I used it to select unique and well-spaced colors for the 75 topics in my visualization.
8. [Zipfian Academy](http://www.zipfianacademy.com/) - The best Data Science school. 

## Glossary of Fancy Terms
* NMF - [Non-Negative Matrix Factorization](http://en.wikipedia.org/wiki/Non-negative_matrix_factorization)
* TFIDF - [Term Frequency - Inverse Document Frequency](http://en.wikipedia.org/wiki/Tf%E2%80%93idf)
