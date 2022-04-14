# Standard Python libraries.
import os
import sys
import traceback
import urllib.parse
from dataclasses import dataclass
from enum import Enum
from time import sleep
from typing import Optional, ClassVar
from config import *
# Third party Python libraries.
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from pydantic import BaseModel, validator, Field
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
import requests

__version__ = "0.0.1"
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))


# todo best way to manage the resources
# todo test proxy
# todo solve the problem to get the hrml with requests
# todo add logs
#todo add asyncio
#todo add screenshots


class QueryType(Enum):
    ALL_THESE_WORDS_PARAMETER_DESCRIPTION = "Type the important words: tri-colour rat terrier"
    THESE_EXACT_WORDS_PARAMETER_DESCRIPTION = "Put exact words in quotes: \"rat terrier\""
    ANY_OF_THESE_WORDS_PARAMETER_DESCRIPTION = "Type OR between all the words you want: miniature OR standard in search bar"
    NONE_OF_THESE_WORDS_PARAMETER_DESCRIPTION = "Put a minus sign just before words that you don't want: -rodent, -\"Jack Russell\""
    NUMBERS_RANGING_FROM_TO_PARAMETER_DESCRIPTION = "Put two full stops between the numbers and add a unit of measurement: 10..35 kg, £300..£500, 2010..2011 in search bar"
    """
    Type the important words: tri-colour rat terrier
    """
    ALL_THESE_WORDS_PARAMETER = "as_q"
    """
    Put exact words in quotes: "rat terrier
    """
    THESE_EXACT_WORDS_PARAMETER = "as_epq"
    """
    Type OR between all the words you want: miniature OR standard in search bar
    """
    ANY_OF_THESE_WORDS_PARAMETER = "as_oq"
    """
    Put a minus sign just before words that you don't want: -rodent, -Jack Russell
    """
    NONE_OF_THESE_WORDS_PARAMETER = "as_eq"
    """
    Put two full stops between the numbers and add a unit of measurement: 10..35 kg, £300..£500, 2010..2011 in search bar
    """
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
    DESCRIPTION = "Find pages updated within the time that you specify."
    PARAMETER = "as_qdr"
    ANYTIME = "all"
    PAST24Hours = "d"
    PAST_WEEK = "w"
    PAST_MONTH = "m"
    PAST_YEAR = "y"


class SiteOrDomain(BaseModel):
    PARAMETER: ClassVar[str] = "as_sitesearch"
    site_or_domain: str = Field(SITE_OR_DOMAIN_DEFAULT,
                                description="Search one site (like wikipedia.org ) or limit your results to a domain like .edu, .org or .gov")


class TermsAppearing(BaseModel):
    DESCRIPTION = "Search for terms in the whole page, page title or web address, or links to the page you're looking for"
    PARAMETER: ClassVar[str] = "as_occt"
    terms_appearing: str = Field(TERMS_APPEARING_DEFAULT,
                                 description="Search for terms in the whole page, page title or web address, or links to the page you're looking for")


class SafeSearch(Enum):
    DESCRIPTION = "Tell SafeSearch whether to filter sexually explicit content."
    PARAMETER = "safe"
    HIDE_EXPLICIT_RESULT = "safe"
    SHOW_EXPLICIT_RESULT = "images"


class FileType(Enum):
    DESCRIPTION = "Find pages in the format that you prefer."
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


@dataclass
class Result:
    url: Optional[str] = None
    snippet: Optional[str] = None
    title: Optional[str] = None
    html: Optional[str] = None


class GoogleAdvancedSearch():
    def __init__(self):
        self.htmls = None
        self._ua = UserAgent()
        self.google_url = None
        self.results = None

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

    def _get_results_with_http_client(self, google_url: str, with_html: bool, proxy: dict):
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
            if not self.htmls:
                self.htmls = []
            self.htmls.append(google_search_html)
            return self._parse_html(google_search_html, with_html)
        return None

    def _parse_html(self, raw_html: str, with_html: bool) -> list[Result]:
        soup = BeautifulSoup(raw_html, 'html.parser')
        result_block = soup.find_all('div', attrs={'class': 'g'})

        results = []
        for result in result_block:
            link = result.find('a', href=True)
            title = result.find('h3')
            snippet = result.find("div", class_="VwiC3b")

            if link and title and snippet:
                html = None
                if with_html:
                    try:
                        html = requests.get(link["href"]).text
                    except:
                        pass
                    #todo add logs here
                results.append(Result(title=title.text, snippet=snippet.text,
                                      url=link["href"], html=html))
        return results

    def _get_new_browser_session(self, proxy: str, remote: bool):
        options = Options()
        options.add_argument('--headless')
        if remote:
            if proxy != None:
                options.add_argument(f"--proxy-server={proxy}")
            try:

                # url = f"http://{SELENIUM_HUB_HOST}:{SELENIUM_HUB_PORT}/{SELENIUM_HUB_LINK}"
                url = f"http://"

                driver = webdriver.Remote(command_executor=url,
                                          desired_capabilities=DesiredCapabilities.FIREFOX)
                driver.maximize_window()
            except Exception as e:
                print("Failed to connect to selenium hub")
                traceback.print_exc()
                sys.exit()
            return driver

        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        return driver

    def _set_new_search(self):
        self.htmls = []

    def _escape_query(self, query) -> str:
        return urllib.parse.quote(query).replace('%20', '+')

    def search(self, query: str,
               query_type: Optional[QueryType] = QueryType.ALL_THESE_WORDS_PARAMETER,
               language: Optional[str] = Language().language_code,
               region: Optional[str] = Region().region_code,
               last_update: Optional[str] = LastUpdate.ANYTIME.value,
               site_or_domain: Optional[str] = SiteOrDomain().site_or_domain,
               terms_appearing: Optional[str] = TermsAppearing().terms_appearing,
               safe_search: Optional[str] = SafeSearch.SHOW_EXPLICIT_RESULT.value,
               file_type: Optional[FileType] = FileType.ANY_FORMAT.value,
               usage_right: Optional[UsageRight] = UsageRight.NOT_FILTERED_BY_LICENSE.value,
               max_results: Optional[int] = MAX_RESULTS_DEFAULT,
               proxy=None, use_browser: bool = False, with_html: bool = False):

        self._set_new_search()
        language = Language(language_code=language)
        region = Region(region_code=region)

        escaped_search_query = self._escape_query(query)
        google_url = f'https://www.google.com/search?{query_type.value}={escaped_search_query}&' \
                     f'num={max_results}&' \
                     f'{Language.PARAMETER}={language.language_code}&' \
                     f'{Region.PARAMETER}={region.region_code}&' \
                     f'{LastUpdate.PARAMETER.value}={last_update}&' \
                     f'{SiteOrDomain.PARAMETER}={site_or_domain}&' \
                     f'{TermsAppearing.PARAMETER}={terms_appearing}&' \
                     f'{SafeSearch.PARAMETER.value}={safe_search}&' \
                     f'{FileType.PARAMETER.value}={file_type}&' \
                     f'{UsageRight.PARAMETER.value}={usage_right}'

        print(google_url)
        self.google_url = google_url
        if not use_browser:
            proxy = self._create_proxy_for_requests(proxy)
            self.results = self._get_results_with_http_client(google_url, with_html, proxy)
        else:
            driver = self._get_new_browser_session(proxy, False)
            driver.get(google_url)
            sleep(1)
            # agree the google policy
            try:
                driver.find_element(By.ID, AGREE_BUTTON).click()
                sleep(1)
            except:
                pass

            results = []
            while True:
                if not self.htmls:
                    self.htmls = []
                self.htmls.append(driver.page_source)
                driver.execute_script("window.scrollTo(0, 5000)")
                sleep(1)
                results.extend(self._parse_html(driver.page_source, with_html))
                is_there_next_btn = False
                try:
                    driver.find_element(By.ID, NEXT_BUTTON)
                    is_there_next_btn = True
                except:
                    # there is no button next
                    pass
                if len(results) >= max_results or not is_there_next_btn:
                    break
                driver.find_element(By.ID, NEXT_BUTTON).click()
            self.results = results
        return self.results
