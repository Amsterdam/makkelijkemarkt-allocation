import os
from pprint import pprint
import json


class BakBranchesMigration:

    INGNORE_LIST = ["a_indeling.json", "merchant_3000187072.json"]
    FIXTURE_DIR = "../fixtures"

    def __init__(self):
        l = os.listdir(self.FIXTURE_DIR)
        for fix in l:
            fixture_file = os.path.join(self.FIXTURE_DIR, fix)
            if fixture_file.endswith(".json") and fix not in self.INGNORE_LIST:
                print("proccessing ", fixture_file)
                f = open(fixture_file, "r")
                data = json.load(f)
                self.migrate(data, to_file=fixture_file)
                f.close()
            elif os.path.isdir(fixture_file):
                for fix in os.listdir(fixture_file):
                    subf_fixture_file = os.path.join(fixture_file, fix)
                    if (
                        subf_fixture_file.endswith(".json")
                        and fix not in self.INGNORE_LIST
                    ):
                        print("proccessing ", subf_fixture_file)
                        f = open(subf_fixture_file, "r")
                        data = json.load(f)
                        self.migrate(data, to_file=subf_fixture_file)
                        f.close()

    def migrate(self, data, to_file="test.json"):
        for pl in data["marktplaatsen"]:
            try:
                branches = pl["branches"]
                if "bak" in branches:
                    branches.remove("bak")
                    pl["bakType"] = "bak"
            except KeyError:
                pass

        for ond in data["ondernemers"]:
            try:
                branches = ond["voorkeur"]["branches"]
                if "bak" in branches:
                    branches.remove("bak")
                    ond["voorkeur"]["bakType"] = "bak"
            except KeyError:
                pass

        f = open(to_file, "w")
        json.dump(data, f, indent=4)
        f.close()


if __name__ == "__main__":
    BakBranchesMigration()
