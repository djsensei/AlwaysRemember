### Topic Modeling
1. Finalize the topics! I _can_ come back to it, but the pipeline from that point forward will eat up time...
2. Consider stemming the documents? It might take a while, and it might screw up some proper names, but it could also decrease the vocabulary size substantially and make the TFIDF stronger.
3. Explore Guantanamo spelling, since there's a funky a in there sometimes?
4. Explore docs around ~2005 since there's a weird dropoff. Are we scraping full text improperly?

### Analysis
1. Ensure that the same top article isn't returned for every topic (see: state of the union address)
  * If an article appears twice, find the topic that it has a higher score, then take the second article for the other topics. Repeat until unique articles. `len(set(L)) == len(L)`
2. Finish+Test empire plot frequency function
3. Make sure outputs are friendly for pushing to D3 (probably csvs?)
4. See if word count has something to do with how much a document matches the topics. It seems like longer documents have more matches (see: state of the union address...)
  * If so, figure out a way to scale it so the matches are more meaningful. Divide by word count, perhaps?

### Visualization Planning
1. Which visualizations will I focus on?
  1. How will they be laid out?
  2. How interactive will they be?
    * Martini glass style?
  3. What data sources (csvs?) do I need to build to support them?

### Bonus Jazz
1. Proper Name formatting: Write function to parse through cleandocs vs. full text to determine if a word is always capitalized. If so, it's a proper name! Ensure that it is capitalized in the viz too, somehow.
