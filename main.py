import requests
import json
import fileinput

from dota_constants import HeroTranslator

# constants
COUNTER_THRESHOLD = 0.43 # score threshold to be considered a counter to the hero
COUNTERED_THRESHOLD = 0.57 # score threshold to be considered countered by the hero
OD_BASE_URL = "https://api.opendota.com/api"
OD_MATCHUPS_URL = "/heroes/{hero_id}/matchups"



# returns two lists of (hero, winrate) pairs.
# The first list corresponds to heroes countered by the selected hero
# and the second list corresponds to counters to the selected hero.
# Both lists are sorted by counter significance.
def find_counters(matchups_data: list[dict]) -> (list[(int, float)], list[(int, float)]):
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


# prints all matchups for the hero with the given id
def print_matchups(hero_id: int, translator: HeroTranslator):
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
        print_matchup(countered_matchup, translator)

    # print counters
    print("This hero is countered by:")
    for counter_matchup in counters:
        print_matchup(counter_matchup, translator)


# prints the info associated with the matchup argument
def print_matchup(matchup: (int, float), translator: HeroTranslator):
    hero_name = translator.id_to_name(matchup[0])
    winrate = matchup[1]
    print("\t" + hero_name + ":\t" + "{:.2f}".format(winrate * 100) + "%")


# runs one iteration of the command line input loop, calling the
# user's desired command and providing feedback.
# Returns true if the command loop should keep running, false otherwise.
def input_iteration(translator: HeroTranslator) -> bool:
    # take and format user input
    line = input("Enter a command (x to exit): ")
    user_input = line.rstrip().lower()

    if user_input == "x":  # return false, end of command loop
        return False
    elif user_input == "names":  # get all hero names
        translator.print_names()
    else:  # print matchups for the given hero
        hero_id = translator.name_to_id(user_input)

        if hero_id is not None:
            print_matchups(hero_id, translator)
        else:
            print("Hero not found...")

    return True


if __name__ == '__main__':
    print("Welcome to Dota 2 Counters.\n")
    print("Enter a hero name to see their counters or enter 'names' to see a list of all hero names\n")

    # prepare hero name to id translating
    translator = HeroTranslator()

    # maintain the input loop until the user enters "x"
    maintain_input = True
    while maintain_input:
        maintain_input = input_iteration(translator)

