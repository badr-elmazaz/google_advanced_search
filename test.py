from search.google_search import *

google_advanced_search = GoogleAdvancedSearch()
options = GoogleAdvancedSearch.Options(use_default_browser=True)
google_query = GoogleQuery(query='wikipedia')
results = google_advanced_search.search(query=google_query, max_results=-1, options=options)
print(len(results))

