from search.google_search import *


google_advanced_search = GoogleAdvancedSearch()
results = google_advanced_search.search(query="wikipedia", max_results=50, use_browser=True, with_html=True)
print(results)