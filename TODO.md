### Topic Modeling
1. Finalize the topics! I _can_ come back to it, but the pipeline from that point forward will eat up time...

### Analysis
1. Ensure that the same top article isn't returned for every topic (see: state of the union address)
  * If an article appears twice, find the topic that it has a higher score, then take the second article for the other topics. Repeat until unique articles. `len(set(L)) == len(L)`
2. Finish+Test empire plot frequency function
3. Make sure outputs are friendly for pushing to D3 (probably csvs?)

### Visualization Planning
1. Which visualizations will I focus on?
  1. How will they be laid out?
  2. How interactive will they be?
    * Martini glass style?
  3. What data sources (csvs?) do I need to build to support them?
2. Color Scheme! Get a good one with enough colors for all the topics.
