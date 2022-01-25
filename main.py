import requests
import json
import string
import fileinput


# constants
COUNTER_THRESHOLD = 0.43 # score threshold to be considered a counter to the hero
COUNTERED_THRESHOLD = 0.57 # score threshold to be considered countered by the hero
OD_BASE_URL = "https://api.opendota.com/api"
OD_MATCHUPS_URL = "/heroes/{hero_id}/matchups"

# hero name data, stored as dicts
name_to_id_dict = {}  # lower case name to int id
id_to_name_dict = {}  # int id to proper name


# initializes the dict of hero names from the stored json file
def init_dicts():
    # load all hero info from a stored json file
    hero_names_file = open("./heroes.json")
    id_to_name_json = json.load(hero_names_file)

    # form the id to name dict with key, value pairs from the parsed file
    for hero_id_str in id_to_name_json:
        hero_name = id_to_name_json[hero_id_str]["localized_name"]
        hero_id = id_to_name_json[hero_id_str]["id"]

        id_to_name_dict[hero_id] = hero_name

    # form the name to id dict by reversing the key, value pairs of the first dict
    for hero_id in id_to_name_dict:
        hero_name = id_to_name_dict[hero_id].lower()
        name_to_id_dict[hero_name] = hero_id


def name_to_id(hero_name:str) -> int:
    return name_to_id_dict[hero_name.lower()]


def id_to_name(hero_id:int) -> str:
    return id_to_name_dict[hero_id]


# returns two lists of (hero, winrate) pairs.
# The first list corresponds to heroes countered by the selected hero
# and the second list corresponds to counters to the selected hero.
# Both lists are sorted by counter significance.
def find_counters(matchups_data : list[dict]) -> (list[(int, float)], list[(int, float)]):
    countered_heroes = []
    counter_heroes = []

    for matchup in matchups_data:
        winrate = matchup["wins"] / matchup["games_played"]
        matchup_info = (matchup["hero_id"], winrate)

        if winrate >= COUNTERED_THRESHOLD:
            countered_heroes.append(matchup_info)
        elif winrate <= COUNTER_THRESHOLD:
            counter_heroes.append(matchup_info)

    return (countered_heroes, counter_heroes)


def print_matchups(hero_id: int):
    url = OD_BASE_URL + OD_MATCHUPS_URL.replace("{hero_id}", str(hero_id))

    print("Obtaining data from: " + url)

    matchups_page = requests.get(url)

    # check to see if the response code can return a page
    if not matchups_page:
        print("Hero not found, please try again with another name")
        return

    # parse the returned string (array of JSON objects) into a list of dictionaries
    matchups_data = json.loads(matchups_page.text)

    # find all counters and countered heroes for the selected hero
    countered, counters = find_counters(matchups_data)

    # print countered heroes
    print("This hero counters:")
    for countered_matchup in countered:
        print_matchup(countered_matchup)

    # print counters
    print("This hero is countered by:")
    for counter_matchup in counters:
        print_matchup(counter_matchup)


# prints the info associated with the matchup argument
def print_matchup(matchup: (int, float)):
    hero_name = id_to_name(matchup[0])
    winrate = matchup[1]
    print("\t" + hero_name + ":\t" + "{:.2f}".format(winrate * 100) + "%")


if __name__ == '__main__':
    print("Welcome to Dota 2 Counters.\n")

    # prepare hero name to id translating
    init_dicts()

    # give counter information for each hero name the user provides
    print("Enter a hero to see counter relationships for: ")
    for line in fileinput.input():
        hero_id = name_to_id(line.rstrip())
        print_matchups(hero_id)

