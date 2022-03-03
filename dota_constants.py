import json


# This class parses hero id and name data from a file upon initialization.
# This data can then be retrieved via calls to the defined interface.
#
class HeroTranslator:

    # parses all hero data and loads it into member data
    #
    def __init__(self):
        # hero name data, stored as dicts
        self._name_to_id_dict = {}  # lower case name to int id
        self._id_to_name_dict = {}  # int id to proper name
        self._hero_names = [] # alphabetized list of hero names

        # load all hero info from a stored json file
        try:
            with open("./heroes.json") as f:  # ensure that the file is closed if an exception is thrown
                id_to_name_json = json.load(f)
        except OSError:
            print("System Error: Unable to read from heroes.json file")
            return

        # form the id to name dict with key, value pairs from the parsed file
        for hero_id_str in id_to_name_json:
            hero_name = id_to_name_json[hero_id_str]["localized_name"]
            hero_id = id_to_name_json[hero_id_str]["id"]

            self._id_to_name_dict[hero_id] = hero_name

        # form the name to id dict by reversing the key, value pairs of the first dict
        for hero_id in self._id_to_name_dict:
            hero_name = self._id_to_name_dict[hero_id].lower()
            self._name_to_id_dict[hero_name] = hero_id

        # initialize the alphabetized list of hero names
        for name in self._name_to_id_dict.keys():
            self._hero_names.append(name)
        self._hero_names.sort()

    # returns the id associated with the given name (None if no id is found)
    #
    def name_to_id(self, hero_name: str) -> int:
        result = None
        if hero_name in self._name_to_id_dict:
            result = self._name_to_id_dict[hero_name.lower()]

        return result

    # returns the name associated with the given id (None if no name is found)
    def id_to_name(self, hero_id: int) -> str:
        result = None
        if hero_id in self._id_to_name_dict:
            result = self._id_to_name_dict[hero_id]

        return result

    # Prints the parsed names of all heroes from the alphabetical list
    #
    def print_names(self) -> None:
        print("Hero name list: ")
        for name in self._hero_names:
            print("\t" + name)
