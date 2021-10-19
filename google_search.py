# Standard Python libraries.
import uuid
from enum import Enum
from typing import Optional
import urllib.parse
import sys
import os.path as op
import json
import os


# Third party Python libraries.
from bs4 import BeautifulSoup
import requests, lxml

__version__ = "0.0.1"
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))


class QueryType(Enum):
    ALL_THESE_WORDS_PARAMETER_DESCRIPTION = "Type the important words: tri-colour rat terrier"
    THESE_EXACT_WORDS_PARAMETER_DESCRIPTION = "Put exact words in quotes: \"rat terrier\""
    ANY_OF_THESE_WORDS_PARAMETER_DESCRIPTION = "Type OR between all the words you want: miniature OR standard in search bar"
    NONE_OF_THESE_WORDS_PARAMETER_DESCRIPTION = "Put a minus sign just before words that you don't want: -rodent, -\"Jack Russell\""
    NUMBERS_RANGING_FROM_TO_PARAMETER_DESCRIPTION = "Put two full stops between the numbers and add a unit of measurement: 10..35 kg, £300..£500, 2010..2011 in search bar"

    ALL_THESE_WORDS_PARAMETER = "as_q"
    THESE_EXACT_WORDS_PARAMETER = "as_epq"
    ANY_OF_THESE_WORDS_PARAMETER = "as_oq"
    NONE_OF_THESE_WORDS_PARAMETER = "as_eq"
    NUMBERS_RANGING_FROM_PARAMETER = "as_nlo"
    NUMBERS_RANGING_TO_PARAMETER = "as_nhi"


class Query():
    def __init__(self, query: str, query_type: QueryType):
        self.query = query
        self.query_type = query_type


class Language():
    DESCRIPTION = "Find pages in the language that you select."
    PARAMETER = "lr"

    def __init__(self, language_code: Optional[str] = "eng"):
        self.language_code = language_code.lower()
        path = op.join(THIS_FOLDER, "languages.json")
        with open(path) as f:
            data = json.load(f)
        if self.language_code != "eng":
            for item in data:
                if item["code"] == self.language_code:
                    break
            else:
                print("Language not found, eng will set by default")


class Region():
    DESCRIPTION = "Find pages published in a particular region."
    PARAMETER = "cr"
    ANY_REGION = ""

    def __init__(self, region_code: str = ""):
        if region_code == None:
            region_code = ""
        self.region_code = region_code.upper()
        path = op.join(THIS_FOLDER, "countries.json")
        with open(path) as f:
            data = json.load(f)

        if self.region_code != "":
            for item in data:
                if item["code"] == self.region_code:
                    self.region_code = "country" + region_code
                    break
            else:
                print("Region not found, your ip region will be set")


class LastUpdate(Enum):
    DESCRIPTION = "Find pages updated within the time that you specify."
    PARAMETER = "as_qdr"
    ANYTIME = "all"
    PAST24Hours = "d"
    PAST_WEEK = "w"
    PAST_MONTH = "m"
    PAST_YEAR = "y"


class SiteOrDomain():
    DESCRIPTION = "Search one site (like wikipedia.org ) or limit your results to a domain like .edu, .org or .gov"
    PARAMETER = "as_sitesearch"

    def __init__(self, site_or_domain=""):
        # todo regex control input
        self.site_or_domain = site_or_domain


class TermsAppearing():
    DESCRIPTION = "Search for terms in the whole page, page title or web address, or links to the page you're looking for"
    PARAMETER = "as_occt"

    def __init__(self, terms_appearing=""):
        # todo regex control input
        self.terms_appearing = terms_appearing


class SafeSearch(Enum):
    DESCRIPTION = "Tell SafeSearch whether to filter sexually explicit content."
    PARAMETER = "safe"
    HIDE_EXPLICIT_RESULT = "safe"
    SHOW_EXPLICIT_RESULT = "images"


class FileType(Enum):
    DESCRIPTION = "Find pages in the format that you prefer."
    PARAMETER = "as_filetype"
    # IT IS EMPTY STRING
    ANY_FORMAT = ""
    ADOBE_ACROBAT_PDF = "pdf"
    AUTODESK_DWF = "dwf"
    GOOGLE_EARTH_KML = "kml"
    GOOGLE_EARTH_KMZ = "kmz"
    MICROSOFT_EXCEL = "xls"
    MICROSOFT_POWERPOINT = "ppt"
    MICROSOFT_WOERD = "doc"
    RICH_TEXT_FORMAT = "rtf"
    SHOCK_WAVE_FLASH = "swf"


class UsageRight(Enum):
    DESCRIPTION = "Find pages that you are free to use yourself."
    PARAMETER = "tbs"
    # IT IS EMPTY STRING
    NOT_FILTERED_BY_LICENSE = ""
    FREE_USE_OR_SHARE = "sur%3Af"
    FREE_USE_OR_SHARE_EVEN_COMMERCIALY = "sur%3Afc"
    FREE_USE_OR_SHARE_OR_MODIFY = "sur%3Afm"
    FREE_USE_OR_SHARE_OR_MODIFY_EVEN_COMMERCIALY = "sur%3Afmc"


def search(query: Query,
           language: Optional[Language] = Language(),
           region: Optional[Region] = Region(),
           last_update: Optional[LastUpdate] = LastUpdate.ANYTIME,
           site_or_domain: Optional[SiteOrDomain] = SiteOrDomain(),
           terms_appearing: Optional[TermsAppearing] = TermsAppearing(),
           safe_search: Optional[SafeSearch] = SafeSearch.SHOW_EXPLICIT_RESULT,
           file_type: Optional[FileType] = FileType.ANY_FORMAT,
           usage_right: Optional[UsageRight] = UsageRight.NOT_FILTERED_BY_LICENSE,
           num_results: Optional[int] = 10,
           proxy=None):
    # encode url with %values
    print(f"query = {query}")
    escaped_search_query = urllib.parse.quote(query.query).replace('%20', '+')

    google_url = f'https://www.google.com/search?{query.query_type.value}={escaped_search_query}&' \
                 f'num={num_results}&' \
                 f'{Language.PARAMETER}={language.language_code}&' \
                 f'{Region.PARAMETER}={region.region_code}&' \
                 f'{LastUpdate.PARAMETER.value}={last_update.value}&' \
                 f'{SiteOrDomain.PARAMETER}={site_or_domain.site_or_domain}&' \
                 f'{TermsAppearing.PARAMETER}={terms_appearing.terms_appearing}&' \
                 f'{SafeSearch.PARAMETER.value}={safe_search.value}&' \
                 f'{FileType.PARAMETER.value}={file_type.value}&' \
                 f'{UsageRight.PARAMETER.value}={usage_right.value}'

    def fetch_results():
        #todo optimize proxy
        p=None
        if proxy is not None:
                p = {"http": proxy}
                print(f"Im using with this proxy: {p}")
        user_agent = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/61.0.3163.100 Safari/537.36'}
        print(f"Url: {google_url}")
        response = None
        try:
            response = requests.get(google_url, proxies=p, headers=user_agent)

            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh)
        except requests.exceptions.ConnectionError as errc:
            print("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)

        return response.text

    def parse_results(raw_html):
        soup = BeautifulSoup(raw_html, 'html.parser')
        result_block = soup.find_all('div', attrs={'class': 'g'})

        from google_search.search import Item
        for result in result_block:
            link = result.find('a', href=True)
            title = result.find('h3')
            snippet = result.find("div", class_="VwiC3b")
            if link and title and snippet:
                yield Item(id=str(uuid.uuid4()), title=title.text.strip(), snippet=snippet.text.strip(),
                           url=link['href'])

    html = fetch_results()
    return list(parse_results(html))


if __name__ == '__main__':
    print(search(query=Query(sys.argv[1], QueryType.ALL_THESE_WORDS_PARAMETER), num_results=int(sys.argv[3]),
                 language=Language(sys.argv[2])))
