# this file defines a few different modes indicated by an enum

from enum import Enum

class Mode(Enum):
    OD_API = 1  # Open Dota API-mode (raw winrate)
    OD_SCRAPE = 2  # Open Dota web-scrape (uses a statistical measure)
    DB_SCRAPE = 3  # Dotabuff webs-scrape (uses a statistical measure)
