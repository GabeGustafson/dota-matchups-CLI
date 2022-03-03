import requests
import json
from bs4 import BeautifulSoup
import re

from dota_constants import HeroTranslator
from modes import Mode

# constants
COUNTER_THRESHOLD = 0.40  # score threshold to be considered a counter to the hero
COUNTERED_THRESHOLD = 0.60  # score threshold to be considered countered by the hero
OD_API_URL = "https://api.opendota.com/api/heroes/{}/matchups"

DB_SCRAPE_URL = "https://www.dotabuff.com/heroes/{}/counters"


# This class allows the printing of counters for a given hero.
# The manner in which counters are obtained depends on the mode of the object.
#
class CounterPrinter:
    def __init__(self, hero_trans: HeroTranslator, mode=Mode.OD_API):
        self._trans = hero_trans

        self._mode = mode
        self._update_parser()  # create counter parser

    # Changes the current mode (see modes.py)
    #
    def set_mode(self, new_mode):
        self._mode = new_mode
        self._update_parser()

    # prints all matchups for the hero with the given id based on the currently assigned mode
    #
    def print_counters(self, hero_id: int):
        # computes the counters and stores them based on the current mode
        counters, countered = self._parser.compute_counters(hero_id)

        # print countered heroes
        print("This hero counters:")
        self._print_matchup_list(countered)

        # print counters
        print("This hero is countered by:")
        self._print_matchup_list(counters)

    # prints all match-ups in the given list
    #
    def _print_matchup_list(self, matchup_list: list[(int, float)]):

        for hero_id, winrate in matchup_list:
            hero_name = self._trans.id_to_name(hero_id)
            print("\t" + hero_name + ":\t" + "{:.2f}".format(winrate * 100) + "%")

    # Creates a new parser for this object based on the current mode.
    #
    def _update_parser(self):
        if self._mode is Mode.OD_API:
            self._parser = ODAPIParser(self._trans)
        elif self._mode is Mode.DB_SCRAPE:
            self._parser = DBSCRAPEParser(self._trans)
        elif self._mode is Mode.OD_SCRAPE:
            self._parser = ODSCRAPEParser(self._trans)
        else:
            self._parser = None


# This class defines an interface for parsing counters using both APIs and
# web-scraping techniques. See children classes below for implementations.
#
class CounterParser:
    def __init__(self, hero_trans: HeroTranslator):
        self._trans = hero_trans

        # establish where the most recently parsed counter information should be stored
        self.counters = []
        self.countered = []

    # Obtains all matchups and then finds counters among them for the given hero id.
    # These operations depend on the parser type (see implementations below).
    #
    # Returns (list of countering heroes, list of countered heroes).
    #
    def compute_counters(self, hero_id: int) -> (list, list):
        matchups_data = self._get_matchups(hero_id)

        self._find_counters(matchups_data)

        return self.counters, self.countered

    # ABSTRACT: Returns all matchups data for a given hero.
    #
    def _get_matchups(self, hero_id: int):
        return None

    # ABSTRACT: Initializes the counter member-lists based on the given matchups data.
    #
    def _find_counters(self, matchups_data):
        return

    # Attempts to return the webpage with requests.
    # Returns None on failure, and the page on success
    #
    def _get_page(self, url):
        # attempt to connect using a request
        print("Obtaining data from: " + url)
        try:
            # NOTE: Dotabuff gives code 429 (too many requests) if user agent is not specified.
            matchups_page = requests.get(url, headers={'User-agent': 'GGPlzWork'})

            # check to see if the response code returned a page
            if not matchups_page:
                print("Hero not found, please try again with another name")
                matchups_page = None

        except requests.exceptions.ConnectionError:
            print("Network Error: unable to connect")
            matchups_page = None

        return matchups_page


# This class defines the functionality for parsing data from OpenDota's API.
#
class ODAPIParser(CounterParser):

    # Returns all matchups as a list of dicts from a parsed JSON list.
    #
    def _get_matchups(self, hero_id: int) -> list[dict]:
        # build the url to get the page with
        url = OD_API_URL.format(str(hero_id))

        # request the page, ensuring that it is valid
        matchups_page = self._get_page(url)
        if matchups_page is None:
            return []

        # parse the returned string (array of JSON objects) into a list of dictionaries
        matchups_data = json.loads(matchups_page.text)

        return matchups_data

    # Initializes counters based on the raw winrate for each matchup.
    #
    def _find_counters(self, matchups_data: list[dict]) -> (list[(int, float)], list[(int, float)]):
        countered_heroes = []
        counter_heroes = []

        for matchup in matchups_data:
            winrate = matchup["wins"] / matchup["games_played"]
            matchup_info = (matchup["hero_id"], winrate)

            if winrate >= COUNTERED_THRESHOLD:
                countered_heroes.append(matchup_info)
            elif winrate <= COUNTER_THRESHOLD:
                counter_heroes.append(matchup_info)

        countered_heroes.sort(key=lambda p: p[1], reverse=True)  # sort by best matchups first
        counter_heroes.sort(key=lambda p: p[1])  # sort by worst matchups first

        self.countered = countered_heroes
        self.counters = counter_heroes


# TODO This class defines the functionality for web-scraping Dotabuff.com.
#
class DBSCRAPEParser(CounterParser):
    # ABSTRACT: Returns all matchups data for a given hero.
    #
    def _get_matchups(self, hero_id: int):
        # get the matchups page, ensuring that its valid
        hero_name = self._trans.id_to_name(hero_id).lower().replace(" ", "-")
        matchups_page = self._get_page(DB_SCRAPE_URL.format(hero_name))
        if matchups_page is None:
            return None  # TODO

        # create a Soup object to parse the page with
        matchups_soup = BeautifulSoup(matchups_page.content, 'html.parser')

        # find the tags that give counter information
        counter_tags = matchups_soup.find_all(class_="counter-outline")

        # TODO navigate to children for both sections...

        print(len(counter_tags))
        print(counter_tags)

    # ABSTRACT: Initializes the counter member-lists based on the given matchups data.
    #
    def _find_counters(self, matchups_data):
        return


# TODO This class defines the functionality for web-scraping OpenDota.com.
#
class ODSCRAPEParser(CounterParser):
    # ABSTRACT: Returns all matchups data for a given hero.
    #
    def _get_matchups(self, hero_id: int):
        return None

    # ABSTRACT: Initializes the counter member-lists based on the given matchups data.
    #
    def _find_counters(self, matchups_data):
        return
