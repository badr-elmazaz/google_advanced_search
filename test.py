from search.google_search import *


google_search = GoogleAdvancedSearch()
results = google_search.search(query="wikipedia", use_browser=True)
print(results)