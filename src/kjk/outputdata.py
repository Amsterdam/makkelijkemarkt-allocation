class MarketArangement:
    """
    A MarketArangement is responsible for producing the output JSON structure for KjK.
    For anexample see: 'fixtures/dapp_20211030/a_indeling.json'
    """
    def add_allocation(self):
        pass

    def add_rejection(self):
        pass

    def set_config(self):
        pass


class Allocation:
    """
    An allocation object encapsulates this datastructure:
        {
            "marktId": "16",
            "marktDate": "2021-10-30",
            "plaatsen": [
                "183",
                "185"
            ],
            "ondernemer": {
                "description": "van Kasteelen",
                "erkenningsNummer": "3000187072",
                "plaatsen": [
                    "183",
                    "185"
                ],
                "voorkeur": {
                    "marktId": 16,
                    "erkenningsNummer": "3000187072",
                    "maximum": 2,
                    "id": 1462,
                    "marktDate": null,
                    "anywhere": true,
                    "minimum": 2,
                    "brancheId": "101-agf-exotische-groenten",
                    "parentBrancheId": null,
                    "inrichting": null,
                    "absentFrom": null,
                    "absentUntil": null,
                    "createdAt": "2019-12-12T21:11:37.502Z",
                    "updatedAt": "2019-12-12T21:11:37.502Z",
                    "branches": [
                        "101-agf-exotische-groenten"
                    ],
                    "verkoopinrichting": []
                },
                "sollicitatieNummer": 573,
                "status": "vpl"
            },
            "erkenningsNummer": "3000187072"
        },
    """

    def __init__(self):
        pass


    def to_json(self):
        pass


class Rejection:
    """
    A Rejection object encapsulates this datastrcture
        {
            "marktId": "16",
            "marktDate": "2021-10-30",
            "erkenningsNummer": "0002020002",
            "reason": {
                "code": 2,
                "message": "Geen geschikte locatie gevonden met huidige voorkeuren."
            },
            "ondernemer": {
                "description": "Die Bont",
                "erkenningsNummer": "0002020002",
                "plaatsen": [],
                "voorkeur": {
                    "marktId": 16,
                    "erkenningsNummer": "0002020002",
                    "maximum": 3,
                    "id": 1131,
                    "marktDate": null,
                    "anywhere": true,
                    "minimum": 2,
                    "brancheId": "109-zuivel-eieren",
                    "parentBrancheId": null,
                    "inrichting": "eigen-materieel",
                    "absentFrom": null,
                    "absentUntil": null,
                    "createdAt": "2020-02-03T19:30:46.248Z",
                    "updatedAt": "2021-10-29T13:47:43.373Z",
                    "branches": [
                        "109-zuivel-eieren"
                    ],
                    "verkoopinrichting": [
                        "eigen-materieel"
                    ]
                },
                "sollicitatieNummer": 10340,
                "status": "soll"
            }
        },
    """
    
    def __init__(self):
        pass


    def to_json(self):
        pass

