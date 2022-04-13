import json

CONFIG_JSON_PATH = "config.json"
with open(CONFIG_JSON_PATH) as f:
    CONFIG = json.load(f)

"""
DEFAULT VALUES
"""
LANGUAGE_DEFAULT = CONFIG["google"]["default"]["LANGUAGE_DEFAULT"]
REGION_DEFAULT = CONFIG["google"]["default"]["REGION_DEFAULT"]
MAX_RESULTS_DEFAULT = CONFIG["google"]["default"]["MAX_RESULTS_DEFAULT"]
AGREE_BUTTON = CONFIG["selenium"]["id"]["agree_button"]
NEXT_BUTTON = CONFIG["selenium"]["id"]["next_button"]
PROXY_TEST_URL = "http://www.google.com"
