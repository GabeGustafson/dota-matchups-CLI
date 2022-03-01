from dota_constants import HeroTranslator
from modes import Mode
from counter_parsing import CounterParser


# runs one iteration of the command line input loop, calling the
# user's desired command and providing feedback.
# Returns true if the command loop should keep running, false otherwise.
#
def input_iteration(hero_trans, counter_parse:CounterParser) -> bool:
    # take and format user input
    line = input("Enter a command (x to exit): ")
    user_input = line.strip().lower()

    if user_input == "x":  # return false, end of command loop
        return False
    elif user_input == "names":  # get all hero names
        hero_trans.print_names()
    elif user_input == "modes":  # TODO allow the user to swap between modes
        pass
    else:  # print matchups for the given hero
        hero_id = hero_trans.name_to_id(user_input)

        if hero_id is not None:
            counter_parse.print_counters(hero_id)
        else:
            print("Hero not found...")

    return True


if __name__ == '__main__':
    print("Welcome to the Dota 2 Counters App!\n")

    print("Instructions:")
    print("\tEnter a hero name to see their counters.")
    print("\tEnter 'names' to see a list of all hero names.")
    print("\tEnter 'modes' to see different ways of getting counter information (web-scraping vs. API usage).")
    print()

    # prepare hero name to id translating
    translator = HeroTranslator()

    # prepare a counter parsing object with the default mode and our created translator
    counter_parser = CounterParser(translator)

    # maintain the input loop until the user enters "x"
    maintain_input = True
    while maintain_input:
        maintain_input = input_iteration(translator, counter_parser)

