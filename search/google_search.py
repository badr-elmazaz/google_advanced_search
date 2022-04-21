#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""This module is used to search for a given query in Google, Bing and DuckDuckGo."""

# Standard Python libraries.
import os
import urllib.parse
from dataclasses import dataclass
from enum import Enum
from time import sleep
from typing import Optional, ClassVar, Union

# Third party Python libraries.
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from pydantic import BaseModel, validator, Field
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import requests
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Own Modules
from config import *

__author__ = "Badr El Mazaz"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Badr El Mazaz"
__email__ = "badr.elmazaz@gmail.com"
__status__ = "Development"


THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))


# todo best way to manage the resources
# todo test proxy
# todo solve the problem to get the hrml with requests
# todo add logs
# todo add asyncio aiohttp for requests
# todo add screenshots
# todo add first results feature
# todo add other search engines
# todo add tests
# todo get all pages results with max results equals to -1
# todo set custom exceptions
# todo add python documentation
# todo add option to get html webpage also with selenium
# todo use python test module to test the code


class QueryType(Enum):
    """
    as_q:
        Type the important words: tri-colour rat terrier
    as_epq:
        Put exact words in quotes: "rat terrier
    as_oq:
        Type OR between all the words you want: miniature OR standard in search bar
    as_eq:
        Put a minus sign just before words that you don't want: -rodent, -Jack Russell
    as_nlo, as_nhi:
        Put two full stops between the numbers and add a unit of measurement: 10..35 kg, £300..£500, 2010..2011 in search bar
    """
    ALL_THESE_WORDS_PARAMETER = "as_q"
    THESE_EXACT_WORDS_PARAMETER = "as_epq"
    ANY_OF_THESE_WORDS_PARAMETER = "as_oq"
    NONE_OF_THESE_WORDS_PARAMETER = "as_eq"
    NUMBERS_RANGING_FROM_PARAMETER = "as_nlo"
    NUMBERS_RANGING_TO_PARAMETER = "as_nhi"


class Language(BaseModel):
    PARAMETER: ClassVar[str] = "lr"
    language_code: str = Field(LANGUAGE_CODE_DEFAULT, description="Find pages in the language that you select.")

    @validator("language_code")
    def validate_language_code(cls, language_code):
        language_code = language_code.lower().strip()
        if language_code == LANGUAGE_CODE_DEFAULT:
            return "lang_" + LANGUAGE_CODE_DEFAULT

        if language_code in LANGUAGES:
            return "lang_" + language_code

        else:
            return "lang_" + LANGUAGE_CODE_DEFAULT


class Region(BaseModel):
    PARAMETER: ClassVar[str] = "cr"
    region_code: str = Field(REGION_CODE_DEFAULT, description="Find pages published in a particular region.")

    @validator("region_code")
    def validate_language_code(cls, region_code):
        ANY_REGION = ""
        region_code = region_code.upper().strip()
        if region_code == ANY_REGION:
            return "country" + REGION_CODE_DEFAULT

        if region_code in COUNTRIES:
            return "country" + region_code
        else:
            return ANY_REGION


class LastUpdate(Enum):
    """Find pages updated within the time that you specify."""
    PARAMETER = "as_qdr"
    ANYTIME = "all"
    PAST24Hours = "d"
    PAST_WEEK = "w"
    PAST_MONTH = "m"
    PAST_YEAR = "y"


class SiteOrDomain(BaseModel):
    """Search one site (like wikipedia.org ) or limit your results to a domain like .edu, .org or .gov"""
    PARAMETER: ClassVar[str] = "as_sitesearch"
    site_or_domain: str = SITE_OR_DOMAIN_DEFAULT


class TermsAppearing(BaseModel):
    """Search for terms in the whole page, page title or web address, or links to the page you're looking for"""
    PARAMETER: ClassVar[str] = "as_occt"
    terms_appearing: str = TERMS_APPEARING_DEFAULT


class SafeSearch(Enum):
    """Tell SafeSearch whether to filter sexually explicit content."""
    PARAMETER = "safe"
    HIDE_EXPLICIT_RESULT = "safe"
    SHOW_EXPLICIT_RESULT = "images"


class FileType(Enum):
    """Find pages in the format that you prefer."""
    PARAMETER = "as_filetype"
    ANY_FORMAT = ""
    ADOBE_ACROBAT_PDF = "pdf"
    AUTODESK_DWF = "dwf"
    GOOGLE_EARTH_KML = "kml"
    GOOGLE_EARTH_KMZ = "kmz"
    MICROSOFT_EXCEL = "xls"
    MICROSOFT_POWERPOINT = "ppt"
    MICROSOFT_WORD = "doc"
    RICH_TEXT_FORMAT = "rtf"
    SHOCK_WAVE_FLASH = "swf"


class UsageRight(Enum):
    PARAMETER = "tbs"
    NOT_FILTERED_BY_LICENSE = ""
    FREE_USE_OR_SHARE = "sur%3Af"
    FREE_USE_OR_SHARE_EVEN_COMMERCIALY = "sur%3Afc"
    FREE_USE_OR_SHARE_OR_MODIFY = "sur%3Afm"
    FREE_USE_OR_SHARE_OR_MODIFY_EVEN_COMMERCIALLY = "sur%3Afmc"


class GoogleQuery(BaseModel):
    query: str = Field(QUERY_DEFAULT, description="The query string you want to search for.")
    query_type: QueryType = QueryType.ALL_THESE_WORDS_PARAMETER
    language: Language = Language()
    region: Region = Region()
    last_update: LastUpdate = LastUpdate.ANYTIME
    site_or_domain: SiteOrDomain = SiteOrDomain()
    terms_appearing: TermsAppearing = TermsAppearing()
    safe_search: SafeSearch = SafeSearch.SHOW_EXPLICIT_RESULT
    file_type: FileType = FileType.ANY_FORMAT
    usage_right: UsageRight = UsageRight.NOT_FILTERED_BY_LICENSE


class BingQuery(BaseModel):
    pass


class DuckDuckGoQuery(BaseModel):
    pass


@dataclass
class Result:
    url: Optional[str] = None
    snippet: Optional[str] = None
    title: Optional[str] = None
    html: Optional[str] = None


class GoogleAdvancedSearch:
    browser_delay = BROWSER_DELAY_DEFAULT
    # google_url = GOOGLE_URL_DEFAULT

    def __init__(self):
        self.htmls = None
        self._ua = UserAgent()
        self.google_url = None
        self.results = None

    class Options(BaseModel):
        proxy: str = None
        use_default_browser: bool = False
        with_html: bool = False
        _web_driver = None

        # @validator("web_driver")
        # def validate_web_driver(cls, web_driver, values):
        #     if values["use_default_browser"] and web_driver:
        #         raise ValueError(
        #             "You can't use a web driver with the default browser, they are mutually exclusive values")
        #     if web_driver:
        #         try:
        #             web_driver.get("https://www.google.com")
        #         except:
        #             raise ValueError("The web driver is not valid")
        #     return web_driver

        @property
        def web_driver(self):
            return self._web_driver

        @web_driver.setter
        def web_driver(self, web_driver):
            """Validate web driver If the user changes it after he set already one before"""
            if web_driver and self.use_default_browser:
                raise ValueError(
                    "You can't use a web driver with the default browser, they are mutually exclusive values")
            if web_driver:
                try:
                    web_driver.get("https://www.google.com")
                except:
                    raise ValueError("The web driver is not valid")
            self._web_driver = web_driver

    def _create_proxy_for_requests(self, proxy: str) -> dict:
        if not proxy:
            return None
        # normalize proxy
        proxy = proxy.replace("http://", "").replace("https://", "")
        proxy_dict = {
            "http": f"http://{proxy}",
            "https": f"https://{proxy}"
        }
        return proxy_dict

    def _is_a_valid_proxy(self, proxy: dict) -> bool:
        if not proxy:
            return False
        try:
            response = requests.get(PROXY_TEST_URL, proxies=proxy)
            if response.ok:
                return True
            return False
        except:
            return False

    def _fetch_htmls_with_http_client(self, google_url: str, proxy: dict) -> list[str]:
        def fetch_results():
            headers = {
                'User-Agent': self._ua.chrome
            }
            try:
                return requests.get(google_url, proxies=proxy, headers=headers).text
            except:
                return None

        google_search_html = fetch_results()
        if google_search_html:
            return [google_search_html]

        return None

    def _do_google_search_with_browser(self, driver, search: GoogleQuery):
        driver.get(self.google_url)
        sleep(self.browser_delay)
        # agree the google policy
        try:
            driver.find_element(By.ID, AGREE_BUTTON).click()
            sleep(self.browser_delay)
        except:
            pass
        # WebDriverWait(driver, BROWSER_DELAY_DEFAULT).until(
        #     EC.presence_of_element_located((By.NAME, "q"))).send_keys(search.query, Keys.ENTER)
        # WebDriverWait(driver, BROWSER_DELAY_DEFAULT).until(
        #     EC.presence_of_element_located((By.ID, "hdtb-tls"))).click()
        print()

    def _fetch_htmls_and_save_results_with_browser(self, search: GoogleQuery, with_html: bool, proxy: str,
                                                   max_results: int, options: Options):
        driver = self._get_new_browser_session(proxy, options)
        # self._do_google_search_with_browser(driver, search)
        if not driver:
            return None
        driver.get(self.google_url)
        sleep(self.browser_delay)
        # agree the google policy
        try:
            driver.find_element(By.ID, AGREE_BUTTON).click()
            sleep(self.browser_delay)
        except:
            pass
        while True:
            driver.execute_script("window.scrollTo(0, 5000)")
            sleep(self.browser_delay)
            partial_results = self._parse_html_in_results(driver.page_source, with_html, max_results)
            # max results reached
            if not partial_results:
                break
            self.results.extend(partial_results)
            self.htmls.append(driver.page_source)
            is_there_next_btn = False
            try:
                driver.find_element(By.ID, NEXT_BUTTON)
                is_there_next_btn = True
            except:
                # there is no button next
                pass
            if not is_there_next_btn:
                break
            driver.find_element(By.ID, NEXT_BUTTON).click()
        driver.quit()

    def _parse_html_in_results(self, raw_html: str, with_html: bool, max_results: int) -> list[Result]:
        results = []
        if len(self.results) < max_results or max_results == -1:
            soup = BeautifulSoup(raw_html, 'html.parser')
            #todo remove literals
            result_block = soup.find_all('div', attrs={'class': 'g'})
            for result in result_block:
                link = result.find('a', href=True)
                title = result.find('h3')
                snippet = result.find("div", class_="VwiC3b")

                if link and title and snippet:
                    if len(self.results) + len(results) < max_results or max_results == -1:
                        html = None
                        if with_html:
                            try:
                                html = requests.get(link["href"]).text
                            except:
                                pass
                            # todo add logs here
                        results.append(Result(title=title.text, snippet=snippet.text,
                                              url=link["href"], html=html))
                    else:
                        break
        return results

    def _get_new_browser_session(self, proxy: str, options: Options):
        if options.web_driver:
            return options.web_driver
        chrome_options = ChromeOptions()
        # chrome_options.add_argument('--headless')
        if proxy:
            chrome_options.add_argument(f"--proxy-server={proxy}")
        try:
            driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        except:
            print("Error: Can't initialize default chrome driver")
            driver = None
        return driver

    def _set_new_search(self):
        self.htmls = []
        self.results = []

    def _escape_query(self, query) -> str:
        return urllib.parse.quote(query).replace('%20', '+')

    def _validate_inputs(self, max_results: int):
        if max_results == 0 or max_results < -1 or not isinstance(max_results, int):
            print(
                f"max_results must be an integer greater than 0 or -1, I will use default value:\t{MAX_RESULTS_DEFAULT}")
            max_results = MAX_RESULTS_DEFAULT
        return max_results

    def _bing_search(self, search: BingQuery):
        pass

    def _duckduckgo_search(self, search: DuckDuckGoQuery):
        pass

    def _google_search(self, search:  GoogleQuery, max_results: int, options: Options):

        max_results_in_query = max_results if max_results != -1 else 100
        escaped_search_query = self._escape_query(search.query)
        google_url = f'https://www.google.com/search?{search.query_type.value}={escaped_search_query}&' \
                     f'num={max_results_in_query}&' \
                     f'{Language.PARAMETER}={search.language.language_code}&' \
                     f'{Region.PARAMETER}={search.region.region_code}&' \
                     f'{LastUpdate.PARAMETER.value}={search.last_update.value}&' \
                     f'{SiteOrDomain.PARAMETER}={search.site_or_domain.site_or_domain}&' \
                     f'{TermsAppearing.PARAMETER}={search.terms_appearing}&' \
                     f'{SafeSearch.PARAMETER.value}={search.safe_search.value}&' \
                     f'{FileType.PARAMETER.value}={search.file_type.value}&' \
                     f'{UsageRight.PARAMETER.value}={search.usage_right.value}'

        print(f"Search URL ==> {google_url}")
        self.google_url = google_url
        if not options.use_default_browser:
            proxy_dict = self._create_proxy_for_requests(options.proxy)
            self.htmls = self._fetch_htmls_with_http_client(google_url, proxy_dict)
            for html in self.htmls:
                results = self._parse_html_in_results(html, options.with_html, max_results)
                self.results.extend(results)
        else:
            self._fetch_htmls_and_save_results_with_browser(search, options.with_html, options.proxy, max_results,
                                                            options)
        return self.results

    def search(self, query: Union[GoogleQuery, BingQuery, DuckDuckGoQuery],
               max_results: Optional[int] = MAX_RESULTS_DEFAULT,
               options=Options()):
        self._set_new_search()
        max_results = self._validate_inputs(max_results)

        if isinstance(query, GoogleQuery):
            self._google_search(query, max_results, options)
