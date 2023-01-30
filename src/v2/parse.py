import datetime
import json
from collections import defaultdict

from v2.branche import Branche
from v2.kramen import Kraam
from v2.ondernemers import Ondernemer
from v2.conf import logger, Status, BAK_TYPE_BRANCHE_IDS


class Parse:
    def __init__(self, input_data=None, json_file=None):
        self.branches = []
        self.branches_map = {}
        self.rows = []
        self.ondernemers = []
        self.markt_meta = {}

        if json_file:
            input_data = self.load_json_file(json_file)
            input_data = input_data.get('data', {})
        self.input_data = input_data or {}
        self.parse_data()

    def load_json_file(self, json_file):
        with open(json_file, 'r') as f:
            input_data = json.load(f)
        return input_data

    def parse_branches(self):
        for branche in self.input_data['branches']:
            new_branche = Branche(
                id=branche['brancheId'],
                verplicht=branche.get('verplicht', False),
                max=branche.get('maximumPlaatsen'),
            )
            self.branches.append(new_branche)
            self.branches_map[branche['brancheId']] = new_branche

    def parse_rows(self):
        for input_row in self.input_data['rows']:
            row = []
            for kraam in input_row:
                kraam_props = {}

                branche_id = next(iter(kraam.get('branches')), None)
                branche = (self.branches_map[branche_id] if branche_id and branche_id not in BAK_TYPE_BRANCHE_IDS
                           else Branche())

                bak_type = kraam['bakType']
                if bak_type == 'bak':
                    kraam_props['bak_licht'] = True
                    kraam_props['bak'] = True
                elif bak_type == 'bak-licht':
                    kraam_props['bak_licht'] = True

                if 'eigen-materieel' in kraam['verkoopinrichting']:
                    kraam_props['evi'] = True

                row.append(Kraam(
                    id=kraam['plaatsId'],
                    branche=branche,
                    **kraam_props,
                ))
            self.rows.append(row)

    def parse_data(self):
        """
        'naam', 'marktId', 'marktDate', 'markt', 'marktplaatsen', 'rows', 'branches', 'obstakels',
        'paginas', 'aanmeldingen', 'voorkeuren', 'ondernemers', 'aanwezigheid', 'aLijst', 'mode'
        """
        # input_data = self.input_data
        self.markt_meta = self.input_data['markt']
        self.parse_branches()
        self.parse_rows()
        self.parse_ondernemers()

    def parse_ondernemers(self):
        plaatsvoorkeuren_map = defaultdict(list)
        for voorkeur in self.input_data['voorkeuren']:
            plaatsvoorkeuren_map[voorkeur['erkenningsNummer']].append(voorkeur['plaatsId'])

        a_list = {ondernemer['erkenningsNummer'] for ondernemer in self.input_data['aLijst']}

        not_present = {rsvp['erkenningsNummer'] for rsvp in self.input_data['aanwezigheid'] if not rsvp['attending']}
        present = {rsvp['erkenningsNummer'] for rsvp in self.input_data['aanwezigheid'] if rsvp['attending']}

        for ondernemer_data in self.input_data['ondernemers']:
            voorkeur = ondernemer_data.get('voorkeur', {})
            erkenningsnummer = ondernemer_data['erkenningsNummer']

            if erkenningsnummer in not_present:
                # logger.log(f"Ondernemer {erkenningsnummer} not present today")
                continue

            if erkenningsnummer not in present:
                if ondernemer_data['status'] in ['vpl', 'eb', 'tvpl', 'tvplz', 'exp', 'expf']:
                    logger.log(f"VPH {ondernemer_data['sollicitatieNummer']} not in presence list "
                               f"so implicitly present")
                    pass
                else:
                    logger.log(f"SOLL {ondernemer_data['sollicitatieNummer']} not in presence list "
                               f"so implicitly absent")
                    continue

            absent_from = voorkeur.get('absentFrom')
            absent_until = voorkeur.get('absentUntil')
            if absent_from and absent_until:
                absent_from_date = datetime.date.fromisoformat(absent_from)
                absent_until_date = datetime.date.fromisoformat(absent_until)
                if absent_from_date <= datetime.date.today() < absent_until_date:
                    logger.log(f"Ondernemer {erkenningsnummer} - {ondernemer_data['sollicitatieNummer']} "
                               f"langdurig afwezig)")
                    continue

            branche_id = next(iter(voorkeur.get('branches', [])), None)
            branche = self.branches_map.get(branche_id, Branche()) if branche_id else Branche()

            ondernemer_props = {}
            bak_type = voorkeur.get('bakType')
            if bak_type == 'bak-licht':
                ondernemer_props['bak_licht'] = True
            elif bak_type == 'bak':
                ondernemer_props['bak'] = True

            if 'eigen-materieel' in voorkeur.get('verkoopinrichting', []):
                ondernemer_props['evi'] = True

            if a_list and ondernemer_data['status'] == Status.SOLL.value:
                if erkenningsnummer in a_list:
                    status = Status.SOLL
                else:
                    status = Status.B_LIST
            else:
                status = Status(ondernemer_data['status'])

            ondernemer = Ondernemer(
                rank=ondernemer_data['sollicitatieNummer'],
                erkenningsnummer=erkenningsnummer,
                description=ondernemer_data['description'],
                branche=branche,
                status=status,
                prefs=plaatsvoorkeuren_map[erkenningsnummer],
                own=ondernemer_data['plaatsen'],
                min=voorkeur.get('minimum', 1),
                max=voorkeur.get('maximum', 10),
                anywhere=voorkeur.get('anywhere'),
                **ondernemer_props,
            )
            self.ondernemers.append(ondernemer)
