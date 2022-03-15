# This file defines a few different modes for obtaining matchups as well as
# a description for each one

from enum import Enum, unique

@unique
class Mode(Enum):
    DB_SCRAPE = 1  # Dotabuff webs-scrape (uses a statistical measure)
    OD_API = 2  # OpenDota API-mode (raw winrate)
    OD_SCRAPE = 3  # OpenDota web-scrape (uses a statistical measure)


# Returns a string describing both the mode of data collection and the semantics of the data
# displayed for the given mode.
#
def describe_mode(mode: Mode):
    if mode == Mode.DB_SCRAPE:
        return "Obtain advantage-scores in public matches from Dotabuff (with web-scraping techniques)"
    elif mode == Mode.OD_API:
        return "Obtain raw winrates in professional matches from OpenDota (with the OpenDota API)"
    elif mode == Mode.OD_SCRAPE:
        return ""  # TODO
    else:
        return ""

