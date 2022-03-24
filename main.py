# Author: Gabriel Gustafson
#
# Note: the heroes.json file was obtained from the one built at https://github.com/odota/dotaconstants

import modes
from modes import Mode
from dota_constants import HeroTranslator
from counter_parsing import CounterPrinter


# Prints a menu that allows the user to change the mode for obtaining and analyzing counters
# (webscraping, API, etc.)
#
def mode_menu(counter_print: CounterPrinter):
    print("\nCurrent Mode:", counter_print.mode.name)
    print()

    print("Select one of the following modes for analyzing counters by entering the corresponding key:")
    print("\t", Mode.DB_SCRAPE.name, "-", modes.describe_mode(Mode.DB_SCRAPE))
    print("\t", Mode.OD_API.name, "-", modes.describe_mode(Mode.OD_API))

    mode_input = input("\nEnter mode key: ")

    if mode_input == Mode.DB_SCRAPE.name:
        counter_print.set_mode(Mode.DB_SCRAPE)
    elif mode_input == Mode.OD_API.name:
        counter_print.set_mode(Mode.OD_API)
    else:
        print("Unable to recognize: {}, please try again with a key from the list.".format(mode_input))

# runs one iteration of the command line input loop, calling the
# user's desired command and providing feedback.
# Returns true if the command loop should keep running, false otherwise.
#
def input_iteration(hero_trans, counter_print:CounterPrinter) -> bool:
    # take and format user input
    line = input("\nEnter a command (x to exit): ")
    user_input = line.strip().lower()

    if user_input == "x":  # return false, end of command loop
        return False
    elif user_input == "names":  # get all hero names
        hero_trans.print_names()
    elif user_input == "modes":
        mode_menu(counter_print)
    else:  # print matchups for the given hero
        hero_id = hero_trans.name_to_id(user_input)

        if hero_id is not None:
            counter_print.print_counters(hero_id)
        else:
            print("Hero not found...")

    return True


if __name__ == '__main__':
    print("Welcome to the Dota 2 Matchups App!\n")

    print("Instructions:")
    print("\tEnter a hero name to see their counters.")
    print("\tEnter 'names' to see a list of all hero names.")
    print("\tEnter 'modes' to see different ways of getting counter information (web-scraping vs. API usage).")

    # prepare hero name to id translating
    translator = HeroTranslator()

    # prepare a counter parsing object with the default mode and our created translator
    counter_printer = CounterPrinter(translator)

    # maintain the input loop until the user enters "x"
    maintain_input = True
    while maintain_input:
        maintain_input = input_iteration(translator, counter_printer)
