import requests
import json
from bs4 import BeautifulSoup
import tabulate # dataframe to_markdown dependency
from pandas import DataFrame

from dota_constants import HeroTranslator
from modes import Mode

# constants
COUNTER_THRESHOLD = 0.40  # winrate threshold to be considered a counter to the hero
COUNTERED_THRESHOLD = 0.60  # winrate threshold to be considered countered by the hero
MIN_GAMES = 10  # minimum number of games played to be considered a valid statistic
PRINT_ROW_LIMIT = 5  # max number of rows to print per matchup table

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
        # compute the counters based on the current mode
        counters_table, countered_table = self._parser.get_matchups(hero_id)

        # print all matchup information
        hero_name = self._trans.id_to_name(hero_id)

        print(hero_name + " is countered by:\n")
        print(counters_table.head(PRINT_ROW_LIMIT).to_markdown(index=False))
        print()
        print(hero_name + " counters:\n")
        print(countered_table.head(PRINT_ROW_LIMIT).to_markdown(index=False))

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


# This abstract class defines an interface for parsing counters using both APIs and
# web-scraping techniques. See children classes below for implementations.
#
class CounterParser:
    def __init__(self, hero_trans: HeroTranslator):
        self._trans = hero_trans

        # the most recently parsed matchups are stored in intermediate data structures
        # entry format: (hero name, matchup-score)
        self._counters = []
        self._countered = []

    # ABSTRACT: Returns a string describing the way that counters are scored for this parser.
    #
    def _describe_counters(self) -> str:
        return ""

    # Obtains all matchups and then finds counters among them for the given hero id.
    # These operations depend on the parser type (see implementations below).
    #
    # Returns a pair of dataframes representing countering heroes and countered heroes.
    #
    def get_matchups(self, hero_id: int) -> (DataFrame, DataFrame):
        self._parse_matchups(hero_id)

        df1, df2 = self._create_counters()

        # reset member data
        self._counters = []
        self._countered = []

        return df1, df2

    # ABSTRACT: Initializes data on matchups for a given hero.
    #
    def _parse_matchups(self, hero_id: int):
        return []

    # Returns tabular counter data based on the initialized matchups data.
    #
    def _create_counters(self) -> (DataFrame, DataFrame):
        counters_df = DataFrame(self._counters, columns=["Hero", self._describe_counters()])
        countered_df = DataFrame(self._countered, columns=["Hero", self._describe_counters()])

        return counters_df, countered_df

    # Attempts to return the webpage with requests.
    # Returns None on failure, and the page on success
    #
    def _get_page(self, url):
        # attempt to connect using a request
        print("Obtaining data from: " + url)
        print()

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
    def _describe_counters(self) -> str:
        return "Winrate Percentage"

    # Initializes matchups from a parsed JSON list obtained from the OpenDota API.
    #
    def _parse_matchups(self, hero_id: int):
        # build the url to get the page with
        url = OD_API_URL.format(str(hero_id))

        # request the page, ensuring that it is valid
        matchups_page = self._get_page(url)
        if matchups_page is None:
            return

        # parse the returned string (array of JSON objects) into a list of dictionaries
        matchups_data = json.loads(matchups_page.text)

        # initialize the member data structures
        self._countered, self._counters = self._convert_matchups(matchups_data)

    # Initializes counters based on the raw win-rates for the given matchups.
    #
    def _convert_matchups(self, matchups_data: list[dict]):
        countered_heroes = []
        counter_heroes = []

        for matchup in matchups_data:
            winrate = matchup["wins"] / matchup["games_played"]

            if matchup["games_played"] >= MIN_GAMES:
                if (winrate >= COUNTERED_THRESHOLD) or (winrate <= COUNTER_THRESHOLD):
                    matchup_info = (self._trans.id_to_name(matchup["hero_id"]), "{:.2f}%".format(winrate * 100))
                    if winrate >= COUNTERED_THRESHOLD:
                        countered_heroes.append(matchup_info)
                    else:
                        counter_heroes.append(matchup_info)

        countered_heroes.sort(key=lambda p: float(p[1][:-1]), reverse=True)  # sort by best matchups first
        counter_heroes.sort(key=lambda p: float(p[1][:-1]))  # sort by worst matchups first

        return countered_heroes, counter_heroes


# This class defines the functionality for web-scraping Dotabuff.com.
#
class DBSCRAPEParser(CounterParser):
    # Returns a string describing the way that counters are scored for this parser.
    #
    def _describe_counters(self) -> str:
        return "Advantage Percentage"

    # Returns the matchups data for a given hero as a pair of lists for countered heroes and
    # counter heroes respectively (using the bs4 web-scraping library).
    #
    def _parse_matchups(self, hero_id: int) -> (list, list):
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
        countered_list = self._create_matchups_list(countered_tags)
        counter_list = self._create_matchups_list(counter_tags)

        self._countered, self._counters = countered_list, counter_list

    # returns a list of matchups created from the group of bs4 tags
    #
    def _create_matchups_list(self, tags):
        # parse each counter-hero tag into a name, score pair
        result = []
        for tag in tags[1:]:
            data = tag.findAll("td")

            if len(data) < 3:
                print("Error: Unable to parse Dotabuff.com")
                return []

            hero_name = str(data[1].string)  # Note: Dotabuff fortunately uses the canonical names for heroes

            score_data = list(data[2].children)  # convert children of the score tag to a list
            hero_score = score_data[0]

            result.append((hero_name, hero_score))

        return result


# TODO: This class defines the functionality for web-scraping OpenDota.com.
#
class ODSCRAPEParser(CounterParser):
    # ABSTRACT: Returns a string describing the way that counters are scored for this parser.
    #
    def _describe_counters(self) -> str:
        return ""

    # ABSTRACT: Initializes data on matchups for a given hero.
    #
    def _parse_matchups(self, hero_id: int):
        return None
