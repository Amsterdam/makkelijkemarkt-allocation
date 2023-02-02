import copy
import pandas as pd

from v2.kramen import Kramen
from v2.ondernemers import Ondernemers
from v2.conf import Status, RejectionReason, TraceMixin, ALL_VPH_STATUS, BAK_TYPE_BRANCHE_IDS

pd.set_option('display.max_colwidth', None)  # so auto truncate of broad columns is turned off
pd.set_option('display.max_columns', None)  # so auto truncate of columns is turned off
pd.set_option('display.max_rows', None)  # so auto truncate of rows is turned off
pd.set_option('display.width', 1000)


class Markt(TraceMixin):
    def __init__(self, meta, rows, branches, ondernemers):
        self.afkorting = '4045'
        self.naam = "Plein '40 - '45"
        self.soort = 'dag'
        self.max_aantal_kramen_per_ondernemer = meta.get('maxAantalKramenPerOndernemer') or 1
        self.kramen_per_ondernemer = 1

        self.kramen = Kramen(rows)
        self.branches_map = {}
        for branche in branches:
            self.branches_map[branche.id] = branche
        self.branches = branches
        self.ondernemers = Ondernemers(ondernemers)
        self.rejection_log = []
        self.step = 1
        self.working_copy = []
        self.allocation_hashes = []

        self.trace.set_rows(self.kramen.as_flat_rows())

    def is_allocation_hash_same_as_previous_round(self):
        allocation_hash = self.kramen.calculate_allocation_hash()
        try:
            last_allocation_hash = self.allocation_hashes[-1]
        except IndexError:
            last_allocation_hash = None

        self.trace.log(f"Current hash: {allocation_hash}, last hash {last_allocation_hash}, all: {self.allocation_hashes}")
        if allocation_hash == last_allocation_hash:
            return True
        else:
            self.allocation_hashes.append(allocation_hash)
            return False

    def clear_allocation_hashes(self):
        self.allocation_hashes = []

    def get_working_copy(self, meta_data=None):
        return copy.deepcopy([
            self.kramen,
            self.ondernemers,
            self.branches,
            meta_data,
        ])

    def restore_working_copy(self, working_copy):
        [
            self.kramen,
            self.ondernemers,
            self.branches,
            meta_data,
        ] = copy.deepcopy(working_copy)
        return meta_data

    def report_indeling(self):
        if self.trace.local:
            dataframes = []
            rows = sorted(self.kramen.as_rows(), key=lambda row: int(row[0].id))
            for row in rows:
                display_row = []
                for kraam in row:
                    kraam_data = {
                        'id': kraam.id,
                        'kraam_type': kraam.kraam_type,
                        'branche': kraam.branche.id[:4] if kraam.branche and kraam.branche.verplicht else '',
                        'ondernemer': kraam.ondernemer if kraam.ondernemer else '',
                    }
                    display_row.append(kraam_data)
                display_row.append({'id': '|', 'ondernemer': '|', 'branche': '|', 'kraam_type': '|'})
                df = pd.DataFrame(display_row)
                dataframes.append(df.T)

            combined_df = pd.concat(dataframes, axis=1)
            combined_df.columns = ['' for x in range(len(combined_df.columns))]
            print(combined_df.to_string(), '\n')

    def report_ondernemers(self, **filter_kwargs):
        if self.trace.local:
            ordered_ondernemers = []
            ondernemers = self.ondernemers.select(**filter_kwargs)
            ordered_ondernemers.extend(ondernemer for ondernemer in ondernemers if ondernemer.status in [Status.VPL,
                                                                                                         Status.EB])
            ordered_ondernemers.extend(ondernemer for ondernemer in ondernemers if ondernemer.status in [Status.TVPL,
                                                                                                         Status.TVPLZ])
            ordered_ondernemers.extend(ondernemer for ondernemer in ondernemers if ondernemer.status in [Status.EXP,
                                                                                                         Status.EXPF])
            ordered_ondernemers.extend(ondernemer for ondernemer in ondernemers if ondernemer.status == Status.SOLL)
            ordered_ondernemers.extend(ondernemer for ondernemer in ondernemers if ondernemer.status == Status.B_LIST)
            print(pd.DataFrame(ondernemer.__dict__ for ondernemer in ordered_ondernemers), '\n')
        self.trace.log(f"Rejection log: {self.rejection_log}")

    def get_allocation(self):
        allocation = []
        for ondernemer in self.ondernemers.all():
            if ondernemer.kramen:
                allocation.append({
                    'plaatsen': list(ondernemer.kramen),
                    'erkenningsNummer': ondernemer.erkenningsnummer,
                })
        return allocation

    def get_rejections(self):
        rejections = []
        for ondernemer in self.ondernemers.all():
            if ondernemer.is_rejected:
                rejections.append({
                    'ondernemer': {
                        'description': ondernemer.description,
                        'sollicitatieNummer': ondernemer.rank,
                        'status': ondernemer.status.value,
                    },
                    'reason': {
                        "message": ondernemer.reject_reason.value,
                    },
                })
        return rejections

    def is_allocation_valid(self, **filter_kwargs):
        return self.are_all_ondernemers_allocated(**filter_kwargs)

    def are_all_ondernemers_allocated(self, **filter_kwargs):
        unallocated_vph = self.ondernemers.select(status__in=ALL_VPH_STATUS, allocated=False, **filter_kwargs)
        unallocated_soll_with_anywhere = self.ondernemers.select(status=Status.SOLL, allocated=False,
                                                                 anywhere=True, **filter_kwargs)
        unallocated = [*unallocated_vph, *unallocated_soll_with_anywhere]
        unallocated = [ondernemer for ondernemer in unallocated
                       if not (ondernemer.reject_reason == RejectionReason.LESS_THAN_MIN
                               and self.kramen_per_ondernemer < ondernemer.min)]

        if unallocated:
            self.trace.log(f"WARNING: Not everybody allocated! Unallocated: {unallocated}")
            return False
        return True

    def get_verplichte_branches(self):
        verplichte_branches = [
            branche for branche in self.branches
            if branche.verplicht
            if branche.id not in BAK_TYPE_BRANCHE_IDS  # better handled as KraamTypes, not as verplichte branche
        ]
        # verplichte branche should also include "Experimentele zone" for EXP
        self.trace.log(f"Verplichte branches: {verplichte_branches}")
        self.trace.log(f"Ignoring branches: {BAK_TYPE_BRANCHE_IDS}")
        return verplichte_branches
