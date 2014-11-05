### Scrape Planning
1. What general scraping do I need to do before I'm satisfied with my general corpus?
  1. Additional queries to the main corpus?
  2. Be sure to doublecheck against the existing database so you don't double-dip.
2. What topics get supplementary scraping?
  1. How will I identify them as such? (Probably add an attribute to their mongo records: {'topic_classification':'main_corpus', 'war_on_terror', 'aviation', ...})
3.

### Topic Modeling Planning
1. How powerful does my TFIDF>NMF need to be?
  1. Balancing power with completion speed
    1. Talk to Nick about running it on a big cluster?
  2. Number of features? Number of topics?
    1. If I choose too many topics, will that weaken the important ones?
  3. How soon do I need to finalize my topics so I can focus on tracing them forward in time?
  4. How large of a time-horizon should my initial topic-modeling corpus contain?
    1. Look at the breakdown of articles by month to see the dropoff inflection point?

### Visualization Planning
1. Which visualizations will I focus on?
  1. How will they be laid out?
  2. How interactive will they be?
  3. What data sources (csvs?) do I need to build to support them?
2. What will I build with?
  1. D3? Something else/better?
3. Who can help me make bomb viz?
4. When do I need to start building it to ensure I finish on time?
