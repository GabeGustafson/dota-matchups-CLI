import requests
import json

from dota_constants import HeroTranslator
from modes import Mode

# constants
COUNTER_THRESHOLD = 0.40  # score threshold to be considered a counter to the hero
COUNTERED_THRESHOLD = 0.60  # score threshold to be considered countered by the hero
OD_BASE_URL = "https://api.opendota.com/api"
OD_MATCHUPS_URL = "/heroes/{hero_id}/matchups"


# This class contains a variety of methods for parsing counters using both APIs and
# web-scraping techniques.
#
class CounterParser():
    def __init__(self, hero_trans, mode=Mode.OD_API):
        self._mode = mode
        self._trans = hero_trans

        # establish where the most recently parsed counter information should be stored
        self.counters = []
        self.countered = []

    # Sets the current mode (see modes.py)
    #
    def set_mode(self, new_mode):
        self._mode = new_mode

    # prints all matchups for the hero with the given id based on the currently assigned mode
    #
    def print_counters(self, hero_id: int):
        self._compute_counters(hero_id)

        # print countered heroes
        print("This hero counters:")
        self._print_matchup_list(self.countered)

        # print counters
        print("This hero is countered by:")
        self._print_matchup_list(self.counters)

    # PRIVATE:

    # Attempts to return the webpage with requests.
    # Returns None on failure, and the page on success
    #
    def _get_page(self, url):
        # attempt to connect using a request
        try:
            matchups_page = requests.get(url)

            # check to see if the response code returned a page
            if not matchups_page:
                print("Hero not found, please try again with another name")
                matchups_page = None

        except requests.exceptions.ConnectionError:
            print("Network Error: unable to connect")
            matchups_page = None

        return matchups_page

    # Helper function: Computes all counters based on matchups.
    #
    def _find_counters_OD_API(self, matchups_data: list[dict]) -> (list[(int, float)], list[(int, float)]):
        countered_heroes = []
        counter_heroes = []

        for matchup in matchups_data:
            winrate = matchup["wins"] / matchup["games_played"]
            matchup_info = (matchup["hero_id"], winrate)

            if winrate >= COUNTERED_THRESHOLD:
                countered_heroes.append(matchup_info)
            elif winrate <= COUNTER_THRESHOLD:
                counter_heroes.append(matchup_info)

        countered_heroes.sort(key=lambda p: p[1],
                              reverse=True)  # sort by most significant countered heroes (best matchups first)
        counter_heroes.sort(key=lambda p: p[1])  # sort by most significant counter heroes (worst matchups first)

        self.countered = countered_heroes
        self.counters = counter_heroes

    # Helper function: Returns all matchups.
    #
    def _get_matchups_OD_API(self, hero_id: int):
        # build the url to get the page with
        url = OD_BASE_URL + OD_MATCHUPS_URL.replace("{hero_id}", str(hero_id))

        print("Obtaining data from: " + url)

        # request the page and ensure that it is valid
        matchups_page = self._get_page(url)
        if self._get_page(url) is None:
            return

        # parse the returned string (array of JSON objects) into a list of dictionaries
        matchups_data = json.loads(matchups_page.text)

        return matchups_data

    # Obtains all matchups and then finds counters among them for the given hero id.
    # These operations depend on the given mode.
    #
    def _compute_counters(self, hero_id: int):

        # assess the current mode, then compute counters appropriately
        if self._mode is Mode.OD_API:
            matchups_data = self._get_matchups_OD_API(hero_id)
            self._find_counters_OD_API(matchups_data)
        else:
            pass  # TODO other modes

    # prints all match-ups in the given list
    #
    def _print_matchup_list(self, matchup_list: list[(int, float)]):

        for hero_id, winrate in matchup_list:
            hero_name = self._trans.id_to_name(hero_id)
            print("\t" + hero_name + ":\t" + "{:.2f}".format(winrate * 100) + "%")