import datetime
import json
from collections import defaultdict

from v2.branche import Branche
from v2.kramen import Kraam
from v2.ondernemers import Ondernemer
from v2.conf import TraceMixin, Status, BAK_TYPE_BRANCHE_IDS, ALL_VPH_STATUS, EXP_BRANCHE
from v2.special_conf import weekday_specific_ondernemer_conf

ALL_VPH_STATUS_AS_STR = [status.value for status in ALL_VPH_STATUS]


class Parse(TraceMixin):
    def __init__(self, input_data=None, json_file=None):
        self.trace.set_phase(epic='parse', story='parse')
        self.trace.set_event_phase()
        self.branches = []
        self.branches_map = {}
        self.rows = []
        self.ondernemers = []
        self.markt_meta = {}
        self.blocked_kramen = []
        self.blocked_dates = []

        if json_file:
            self.trace.set_phase(task='read_input_data')
            self.trace.log(f"Use json file: {json_file}")
            input_data = self.load_json_file(json_file)
            input_data = input_data.get('data', {})
        self.input_data = input_data or {}

        markt_date = input_data['marktDate']
        self.trace.log(f"Markt date: {markt_date}")
        self.markt_date = datetime.date.fromisoformat(markt_date)
        self.weekday = self.markt_date.isoweekday()
        self.trace.log(f"Weekday: {self.weekday}")
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
                is_blocked = False
                if kraam['plaatsId'] in self.blocked_kramen:
                    is_blocked = True
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
                    is_blocked=is_blocked,
                    **kraam_props,
                ))
            self.rows.append(row)

    def parse_data(self):
        """
        'naam', 'marktId', 'marktDate', 'markt', 'marktplaatsen', 'rows', 'branches', 'obstakels',
        'paginas', 'aanmeldingen', 'voorkeuren', 'ondernemers', 'aanwezigheid', 'aLijst', 'mode'
        """
        self.parse_markt()
        self.parse_branches()
        self.parse_rows()
        self.parse_ondernemers()
        self.report_ondernemers()

    def parse_markt(self):
        self.markt_meta = self.input_data['markt']
        self.markt_meta['markt_date'] = self.input_data['marktDate']
        self.trace.log(f"Markt {self.markt_meta['naam']} - {self.markt_meta['afkorting']}")
        blocked_kramen = self.markt_meta.get('kiesJeKraamGeblokkeerdePlaatsen')
        self.blocked_kramen = blocked_kramen.split(',') if blocked_kramen else []
        self.trace.log(f"Geblokkeerde kramen {self.blocked_kramen}")
        blocked_dates = self.markt_meta.get('kiesJeKraamGeblokkeerdeData', '')
        self.blocked_dates = blocked_dates.split(',') if blocked_dates else []
        self.trace.log(f"Geblokkeerde datums {self.blocked_dates}")

    def update_ondernemer_data_for_weekday(self, ondernemer_data):
        self.trace.set_phase(epic='parse', story='special_ondernemers', task='set_status_per_day')
        for weekday_specific_ondernemer_props in weekday_specific_ondernemer_conf:
            if self.markt_meta['afkorting'] != weekday_specific_ondernemer_props['markt_afkorting']:
                continue
            if ondernemer_data['sollicitatieNummer'] == weekday_specific_ondernemer_props['sollicitatie_nummer']:
                self.trace.log(f"Set special ondernemer properties for {ondernemer_data['sollicitatieNummer']}")
                self.trace.log(weekday_specific_ondernemer_props)

                weekdays = weekday_specific_ondernemer_props.get('weekdays', '')
                weekdays = weekdays.split(',') if weekdays else []
                if str(self.weekday) in weekdays:
                    plaatsen = weekday_specific_ondernemer_props.get('plaatsen', '')
                    plaatsen = plaatsen.split(',') if plaatsen else []
                    ondernemer_data['plaatsen'] = plaatsen
                    for key, value in weekday_specific_ondernemer_props.items():
                        if key in ['status']:
                            ondernemer_data[key] = value
                        if key in ['anywhere']:
                            voorkeur = ondernemer_data['voorkeur']
                            voorkeur[key] = value

    def parse_ondernemers(self):
        self.trace.set_phase(epic='parse', story='ondernemers')
        plaatsvoorkeuren_map = defaultdict(list)
        for voorkeur in self.input_data['voorkeuren']:
            plaatsvoorkeuren_map[voorkeur['erkenningsNummer']].append(voorkeur['plaatsId'])

        self.trace.set_phase(epic='parse', story='ondernemers', task='determine_a_b')
        a_list = {ondernemer['erkenningsNummer'] for ondernemer in self.input_data['aLijst']}
        has_active_a_b_indeling = self.markt_meta['indelingstype'] == 'a/b-lijst' and bool(a_list)
        self.trace.log(f"has_active_ab_indeling: {has_active_a_b_indeling}")

        not_present = {rsvp['erkenningsNummer'] for rsvp in self.input_data['aanwezigheid'] if not rsvp['attending']}
        present = {rsvp['erkenningsNummer'] for rsvp in self.input_data['aanwezigheid'] if rsvp['attending']}

        for ondernemer_data in self.input_data['ondernemers']:
            voorkeur = ondernemer_data.get('voorkeur', {})
            erkenningsnummer = ondernemer_data['erkenningsNummer']
            rank = ondernemer_data['sollicitatieNummer']
            log_entry = f"Ondernemer {rank} - {ondernemer_data['status']} - {erkenningsnummer}"

            self.trace.set_phase(epic='parse', story='ondernemers', task='check_presence')
            self.update_ondernemer_data_for_weekday(ondernemer_data)
            if erkenningsnummer in not_present:
                continue
            if erkenningsnummer not in present:
                if ondernemer_data['status'] in ALL_VPH_STATUS_AS_STR:
                    self.trace.log(f"{log_entry} not in presence list so implicitly present")
                else:
                    # self.trace.log(f"{log_entry} not in presence list so implicitly absent")
                    continue

            absent_from = voorkeur.get('absentFrom')
            absent_until = voorkeur.get('absentUntil')
            if absent_from and absent_until:
                absent_from_date = datetime.date.fromisoformat(absent_from)
                absent_until_date = datetime.date.fromisoformat(absent_until)
                if absent_from_date <= self.markt_date <= absent_until_date:
                    self.trace.log(f"{log_entry} langdurig afwezig)")
                    continue

            branche_id = next(iter(voorkeur.get('branches', [])), None)
            if ondernemer_data['status'] in [Status.EXP.value, Status.EXPF.value]:
                self.trace.log(f"Explicitly setting branche for {log_entry} to {EXP_BRANCHE}")
                branche_id = EXP_BRANCHE
            branche = self.branches_map.get(branche_id, Branche()) if branche_id else Branche()

            ondernemer_props = {}
            bak_type = voorkeur.get('bakType')
            if bak_type == 'bak-licht':
                ondernemer_props['bak_licht'] = True
            elif bak_type == 'bak':
                ondernemer_props['bak'] = True

            if 'eigen-materieel' in voorkeur.get('verkoopinrichting', []):
                ondernemer_props['evi'] = True

            if has_active_a_b_indeling and ondernemer_data['status'] == Status.SOLL.value:
                if erkenningsnummer in a_list:
                    status = Status.SOLL
                else:
                    status = Status.B_LIST
            else:
                status = Status(ondernemer_data['status'])

            self.trace.set_phase(task='check_anywhere')
            anywhere = voorkeur.get('anywhere')
            if anywhere is None:
                anywhere = False
                self.trace.log(f"{log_entry} is missing anywhere value in profile, so defaulting to False")

            if status in ALL_VPH_STATUS and anywhere:
                self.trace.log(f"{log_entry} is {status.value} with anywhere True, setting to False")
                anywhere = False

            if status == Status.TVPLZ and not anywhere:
                self.trace.log(f"{log_entry} is {status.value} but anywhere not True, setting to True")
                anywhere = True

            self.trace.set_phase(task='check_vph_has_kramen')
            if status in ALL_VPH_STATUS and not ondernemer_data['plaatsen']:
                self.trace.log(f"{log_entry} is {status.value} but no own kramen, so skipping ondernemer")
                continue

            ondernemer = Ondernemer(
                rank=rank,
                erkenningsnummer=erkenningsnummer,
                description=ondernemer_data['description'],
                branche=branche,
                status=status,
                prefs=plaatsvoorkeuren_map[erkenningsnummer],
                own=ondernemer_data['plaatsen'],
                min=voorkeur.get('minimum', 1),
                max=voorkeur.get('maximum', 10),
                anywhere=anywhere,
                raw=ondernemer_data,
                **ondernemer_props,
            )
            self.ondernemers.append(ondernemer)

    def report_ondernemers(self):
        self.trace.set_phase(task='report_ondernemers')
        for ondernemer in self.ondernemers:
            self.trace.log(ondernemer)
