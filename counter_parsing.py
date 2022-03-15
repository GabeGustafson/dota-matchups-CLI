import requests
import json
from bs4 import BeautifulSoup
import re

from dota_constants import HeroTranslator
from modes import Mode

# constants
COUNTER_THRESHOLD = 0.40  # winrate threshold to be considered a counter to the hero
COUNTERED_THRESHOLD = 0.60  # winrate threshold to be considered countered by the hero
MIN_GAMES = 10  # minimum number of games played to be considered a valid statistic

OD_API_URL = "https://api.opendota.com/api/heroes/{}/matchups"
DB_SCRAPE_URL = "https://www.dotabuff.com/heroes/{}/counters"


# This class allows the printing of counters for a given hero.
# The manner in which counters are obtained depends on the mode of the object.
#
class CounterPrinter:
    def __init__(self, hero_trans: HeroTranslator, mode=Mode.DB_SCRAPE):
        self._trans = hero_trans

        self._mode = mode
        self._update_parser()  # create counter parser

    @property
    def mode(self):
        return self._mode

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

        # print the semantics of the counter scoring system for this mode of parser
        print(self._parser.describe_counters())
        print()

        # print countered heroes
        print("This hero counters:")
        self._print_matchup_list(countered)

        # print counters
        print("This hero is countered by:")
        self._print_matchup_list(counters)

    # prints all match-ups in the given list of hero_id, proportional score pairs.
    #
    def _print_matchup_list(self, matchup_list: list[(int, float)]):
        for matchup_id, score in matchup_list:
            hero_name = self._trans.id_to_name(matchup_id)
            print("\t" + hero_name + ":\t" + "{:.2f}".format(score * 100) + "%")

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

    # ABSTRACT: Returns a string describing the way that counters are scored for this parser.
    #
    def describe_counters(self) -> str:
        return ""

    # Obtains all matchups and then finds counters among them for the given hero id.
    # These operations depend on the parser type (see implementations below).
    #
    # Returns (list of countering heroes, list of countered heroes).
    #
    def compute_counters(self, hero_id: int) -> (list, list):
        matchups_data = self._get_matchups(hero_id)

        self._init_counters(matchups_data)

        return self.counters, self.countered

    # ABSTRACT: Returns a group of data on matchups for a given hero.
    #
    def _get_matchups(self, hero_id: int):
        return []

    # ABSTRACT: Initializes the counter member-lists based on the given matchups data.
    #
    def _init_counters(self, matchups_data):
        pass


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

    # Returns a string describing the way that counters are scored for this parser.
    #
    def describe_counters(self) -> str:
        return "FORMAT: Hero Matchup, Winrate"

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
    def _init_counters(self, matchups_data: list[dict]):
        countered_heroes = []
        counter_heroes = []

        for matchup in matchups_data:
            winrate = matchup["wins"] / matchup["games_played"]
            matchup_info = (matchup["hero_id"], winrate)

            if matchup["games_played"] >= MIN_GAMES:
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
    # Returns a string describing the way that counters are scored for this parser.
    #
    def describe_counters(self) -> str:
        return "FORMAT: Hero Matchup, Advantage Percentage"

    # Returns the matchups data for a given hero as a pair of lists for countered heroes and
    # counter heroes respectively (using the bs4 web-scraping library).
    #
    def _get_matchups(self, hero_id: int) -> (list, list):
        # returns a list of matchups created from the group of bs4 tags
        def _create_matchups_list(tags):
            # parse each counter-hero tag into a name, score pair
            result = []
            for tag in tags[1:]:
                data = tag.findAll("td")

                if len(data) < 3:
                    print("Error: Unable to parse Dotabuff.com")
                    return []

                hero_name = str(data[1].string)  # Note: Dotabuff fortunately uses the canonical names for heroes
                hero_id = self._trans.name_to_id(hero_name)

                score_data = list(data[2].children)  # convert children of the score tag to a list
                hero_score = float(score_data[0][:-1]) / 100

                result.append((hero_id, hero_score))

            return result

        # get the matchups page, ensuring that its valid
        hero_name = self._trans.id_to_name(hero_id).lower().replace(" ", "-")
        matchups_page = self._get_page(DB_SCRAPE_URL.format(hero_name))
        if matchups_page is None:
            return [], []

        # create a Soup object to parse the page with
        matchups_soup = BeautifulSoup(matchups_page.content, 'html.parser')

        # find the two sections that show notable matchups
        matchup_sections = matchups_soup.find_all(class_="counter-outline")
        if len(matchup_sections) < 2:
            print("Error: Unable to parse Dotabuff.com")
            return [], []

        # find the tags that give matchup information
        counter_section, countered_section = matchup_sections[0], matchup_sections[1]
        countered_tags = countered_section.find_all("tr")
        counter_tags = counter_section.find_all("tr")

        # form and return the lists of matchups
        countered_list = _create_matchups_list(countered_tags)
        counter_list = _create_matchups_list(counter_tags)

        return countered_list, counter_list

    # Initializes the counter member-lists based on the lists parsed using bs4.
    #
    def _init_counters(self, matchups_data):
        # simply unpack the matchup lists
        self.countered, self.counters = matchups_data




# TODO This class defines the functionality for web-scraping OpenDota.com.
#
class ODSCRAPEParser(CounterParser):
    # ABSTRACT: Returns a string describing the way that counters are scored for this parser.
    #
    def describe_counters(self) -> str:
        return ""

    # ABSTRACT: Returns all matchups data for a given hero.
    #
    def _get_matchups(self, hero_id: int):
        return None

    # ABSTRACT: Initializes the counter member-lists based on the given matchups data.
    #
    def _init_counters(self, matchups_data):
        return
