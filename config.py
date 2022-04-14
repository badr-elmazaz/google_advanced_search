import ujson

CONFIG_JSON_PATH = "config.json"
with open(CONFIG_JSON_PATH) as f:
    CONFIG = ujson.load(f)

with open("./resources/countries.json") as f:
    COUNTRIES = ujson.load(f)
    COUNTRIES = set(k["code"].upper() for k in COUNTRIES)
with open("./resources/languages.json") as f:
    LANGUAGES = ujson.load(f)
    LANGUAGES = set(k["code"].lower() for k in LANGUAGES)

"""
DEFAULT VALUES
"""
LANGUAGE_CODE_DEFAULT = CONFIG["google"]["default"]["LANGUAGE_CODE_DEFAULT"]
REGION_CODE_DEFAULT = CONFIG["google"]["default"]["REGION_CODE_DEFAULT"]
MAX_RESULTS_DEFAULT = CONFIG["google"]["default"]["MAX_RESULTS_DEFAULT"]
SITE_OR_DOMAIN_DEFAULT = CONFIG["google"]["default"]["SITE_OR_DOMAIN_DEFAULT"]
TERMS_APPEARING_DEFAULT = CONFIG["google"]["default"]["TERMS_APPEARING_DEFAULT"]

"""
SEARCH DEFAULT VALUES
"""
AGREE_BUTTON = CONFIG["selenium"]["id"]["agree_button"]
NEXT_BUTTON = CONFIG["selenium"]["id"]["next_button"]
PROXY_TEST_URL = "http://www.google.com"
