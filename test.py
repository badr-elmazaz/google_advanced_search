from search.google_search import *


google_advanced_search = GoogleAdvancedSearch()
results = google_advanced_search.search(query="cubo di rubik", max_results=53, use_browser=True)
print(len(results))