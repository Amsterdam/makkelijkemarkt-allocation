import json
from faker import Faker
from pprint import pprint


class Anonymizer:
    def __init__(self, rot, offset):
        self.fake = Faker(["nl_NL"])
        Faker.seed(666)
        self.name_map = {}
        self.rot = int(rot)
        self.offset = int(offset)

    def _encode_erkennings_nummer(self, erk=None):
        p1 = erk[self.rot :]
        p2 = erk[: (10 - self.rot) * -1]
        s = p1 + p2
        try:
            erk = int(s)
            erk = erk + self.offset
            return str(erk)
        except ValueError:
            pass
        return s

    def __save(self, data, original_filename):
        filename = original_filename.replace(".json", "_a.json")
        f = open(filename, "w")
        json.dump(data, f, indent=4)
        f.close()
        print(f"\nSUCCESS: Geanonimiseerde fixture gesaved: {filename}")

    def process_input(self, filenames):
        for f in filenames:
            _f = open(f, "r")
            data = json.load(_f)
            for obj in data["aanmeldingen"]:
                obj["erkenningsNummer"] = self._encode_erkennings_nummer(
                    obj["erkenningsNummer"]
                )
            for obj in data["voorkeuren"]:
                obj["erkenningsNummer"] = self._encode_erkennings_nummer(
                    obj["erkenningsNummer"]
                )
            for obj in data["aanwezigheid"]:
                obj["erkenningsNummer"] = self._encode_erkennings_nummer(
                    obj["erkenningsNummer"]
                )
            for obj in data["ondernemers"]:
                obj["erkenningsNummer"] = self._encode_erkennings_nummer(
                    obj["erkenningsNummer"]
                )
                obj["voorkeur"]["erkenningsNummer"] = self._encode_erkennings_nummer(
                    obj["voorkeur"]["erkenningsNummer"]
                )
                fake_name = self.fake.last_name()
                self.name_map[obj["description"]] = fake_name
                obj["description"] = fake_name
            for obj in data["aLijst"]:
                obj["erkenningsNummer"] = self._encode_erkennings_nummer(
                    obj["erkenningsNummer"]
                )
                obj["voorkeur"]["erkenningsNummer"] = self._encode_erkennings_nummer(
                    obj["voorkeur"]["erkenningsNummer"]
                )
                try:
                    obj["description"] = self.name_map[obj["description"]]
                except KeyError as e:
                    obj["description"] = "unknown"
            _f.close()
            pprint(self.name_map)
            self.__save(data, f)

    def run(self, filename):
        self.process_input([filename])


if __name__ == "__main__":
    filename = input("Geef het pad naar de fixture a.u.b : ")
    rot = input("Geef een rotatie getal tussen de 0 en 10 : ")
    try:
        if int(rot) < 0 or int(rot) > 10:
            print(f"ERROR: Rotatie moet tussen de 0 en 10 zijn. (gegeven {rot})")
            exit()
        offset = input("Geef een offset getal tussen de 0 en 100 : ")
        if int(offset) < 0 or int(offset) > 100:
            print(f"ERROR: Offset moet tussen de 0 en 100 zijn. (gegeven {offset})")
            exit()
    except ValueError:
        print("Geef numerieke input voor offset en rotatie a.u.b")
        exit()
    a = Anonymizer(rot, offset)
    a.run(filename)
