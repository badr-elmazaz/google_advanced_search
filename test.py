from search.google_search import *



if __name__ == '__main__':
    query_type=QueryType.ALL_THESE_WORDS_PARAMETER
    q = "price bitcoin in usd"
    query=Query(query_type=query_type, query=q)
    language=Language("it")
    region=Region("it")
    last_update=LastUpdate.PAST_24_HOURS
    results=search(query=query, language=language, region=region, last_update=last_update)
    for result in results:
        print(result)
