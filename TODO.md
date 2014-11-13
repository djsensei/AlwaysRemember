## Priority List
1. Run giant modeling TFIDF NMF job on AWS - 100k terms, 200 topics, 100 top words?
  * If that model isn't super great, just stick with the 50 or 100 topic model I already built.
2. Explore 2005 dropoff, find and plug the full_text leak (or figure out why there isn't one)
3. Inspect 100 topic 20k term model: is it better than the 50 topic model?
4. Smooth and Finish analysis pipeline: Output topic term dicts and example articles so that D3 can use them!
  * JSON file secondary to main csv?
5. How to handle smaller-timeframe analysis shortly after attacks in the viz?
  * What about zooming/panning the main timeline?
6. Feedback on presentation, jazz it up. 

## Secondary List
1. Compile "keywords" (Names of "characters"?) that will be familiar to everyone, and automate the process for outputting their topic weights: easy bar graphs!
  * Proper Name Formatting: compare clean text to full text, see how often a word is capitalized.
2. Topic Term lists: remove duplicates ("al", "al qaeda", "qaeda") before displaying...
3. Stemming/Lemmatizing docs before TFIDF? Not sure if there's time to run everything again after that...
