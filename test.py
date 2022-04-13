from search.google_search import *


google_search = GoogleAdvancedSearch()
results = google_search.search(query="wikipedia", max_results=50)
print(results)