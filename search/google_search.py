# Standard Python libraries.
import json
import os
import os.path as op
import sys
import traceback
import urllib.parse
from enum import Enum
from typing import Optional, ClassVar
from time import sleep
import requests
# Third party Python libraries.
from bs4 import BeautifulSoup
from config import *
from pydantic import BaseModel, validator, Field
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from dataclasses import dataclass
from fake_useragent import UserAgent
from webdriver_manager.chrome import ChromeDriverManager

__version__ = "0.0.1"
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

with open("./resources/countries.json") as f:
    countries = json.load(f)
with open("./resources/languages.json") as f:
    languages = json.load(f)


#todo best way to manage the resources
#todo test proxy

class Query():
    def __init__(self, query: str):
        self.query = query


class Language(BaseModel):
    PARAMETER: ClassVar[str] = "lr"
    language_code: str = Field(LANGUAGE_DEFAULT, description="Find pages in the language that you select.")

    @validator("language_code")
    def validate_language_code(cls, language_code):
        if language_code == LANGUAGE_DEFAULT:
            return "lang_" + LANGUAGE_DEFAULT
        language_code = language_code.lower()

        if language_code != LANGUAGE_DEFAULT:
            for language in languages:
                if language["code"] == language_code:
                    return "lang_" + language_code

            else:
                return "lang_" + LANGUAGE_DEFAULT


class Region(BaseModel):
    PARAMETER: ClassVar[str] = "cr"
    ANY_REGION = ""
    region_code: str = Field(REGION_DEFAULT, description="Find pages published in a particular region.")

    @validator("region_code")
    def validate_language_code(cls, region_code):
        ANY_REGION = ""
        if region_code == ANY_REGION:
            return REGION_DEFAULT

        region_code = region_code.upper()

        for country in countries:
            if country["code"] == region_code:
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
    site_or_domain: str = Field("",
                                description="Search one site (like wikipedia.org ) or limit your results to a domain like .edu, .org or .gov")


class TermsAppearing(BaseModel):
    DESCRIPTION = "Search for terms in the whole page, page title or web address, or links to the page you're looking for"
    PARAMETER: ClassVar[str] = "as_occt"
    terms_appearing: str = Field("",
                                 description="Search for terms in the whole page, page title or web address, or links to the page you're looking for")


class SafeSearch(Enum):
    # todo do not show description in json schema
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
    MICROSOFT_WORD = "doc"
    RICH_TEXT_FORMAT = "rtf"
    SHOCK_WAVE_FLASH = "swf"


class UsageRight(Enum):
    # todo do not show parameter in json schema
    PARAMETER: ClassVar[str] = "tbs"
    # IT IS EMPTY STRING
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


class GoogleAdvancedSearch():
    def __init__(self):
        self.htmls = []
        self.ua = UserAgent()
        self.google_url = None


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

    def _get_results_with_http_client(self, google_url: str, proxy: dict):
        def fetch_results():
            headers = {
                'User-Agent': self.ua.chrome
            }
            headers = None
            try:
                return requests.get(google_url, proxies=proxy, headers=headers).text
            except:
                return None

        html = fetch_results()
        if html:
            self.htmls.append(html)
            return self._parse_html(html)
        return None

    def _parse_html(self, raw_html: str):
        soup = BeautifulSoup(raw_html, 'html.parser')
        result_block = soup.find_all('div', attrs={'class': 'g'})

        results = []
        for result in result_block:
            link = result.find('a', href=True)
            title = result.find('h3')
            snippet = result.find("div", class_="VwiC3b")

            if link and title and snippet:
                results.append(Result(title=title.text, snippet=snippet.text,
                                      url=link['href']))
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
               language: Optional[str] = "en",
               region: Optional[str] = "",
               last_update: Optional[str] = LastUpdate.ANYTIME.value,
               site_or_domain: Optional[str] = "",
               terms_appearing: Optional[str] = TermsAppearing().terms_appearing,
               safe_search: Optional[str] = SafeSearch.SHOW_EXPLICIT_RESULT.value,
               file_type: Optional[FileType] = FileType.ANY_FORMAT.value,
               usage_right: Optional[UsageRight] = UsageRight.NOT_FILTERED_BY_LICENSE.value,
               max_results: Optional[int] = MAX_RESULTS_DEFAULT,
               proxy=None, use_browser: bool = False):
        self._set_new_search()

        # if not max_results:
        #     max_results = self.MAX_RESULTS_DEFAULT

        escaped_search_query = self._escape_query(query)
        # todo better way to manage query type
        query_type = "as_q"
        google_url = f'https://www.google.com/search?{query_type}={escaped_search_query}&' \
                     f'num={max_results}&' \
                     f'{Language.PARAMETER}={language}&' \
                     f'{Region.PARAMETER}={region}&' \
                     f'{LastUpdate.PARAMETER.value}={last_update}&' \
                     f'{SiteOrDomain.PARAMETER}={site_or_domain}&' \
                     f'{TermsAppearing.PARAMETER}={terms_appearing}&' \
                     f'{SafeSearch.PARAMETER.value}={safe_search}&' \
                     f'{FileType.PARAMETER.value}={file_type}&' \
                     f'{UsageRight.PARAMETER.value}={usage_right}'

        print(google_url)
        self.google_url=google_url
        if not use_browser:
            proxy = self._create_proxy_for_requests(proxy)
            return self._get_results_with_http_client(google_url, proxy)
        driver = self._get_new_browser_session(proxy, False)
        driver.get(google_url)
        sleep(1)
        #agree the google policy
        try:
            driver.find_element(By.ID, AGREE_BUTTON).click()
            sleep(1)
        except:
            pass

        results = []
        while True:
            self.htmls.append(driver.page_source)
            driver.execute_script("window.scrollTo(0, 5000)")
            sleep(1)
            results.extend(self._parse_html(driver.page_source))
            is_there_next_btn = False
            try:
                driver.find_element(By.ID, NEXT_BUTTON)
                is_there_next_btn = True
            except:
                #there is no button next
                pass
            if len(results) >= max_results or not is_there_next_btn:
                break
            driver.find_element(By.ID, NEXT_BUTTON).click()
        return results
