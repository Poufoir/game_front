from itertools import groupby

from nicegui import ui

from game_front.api_client import ApiClient


class RecapView:
    def __init__(self, api: ApiClient, AUTH_ENABLED: bool = True):
        self.api = api
        self.AUTH_ENABLED = AUTH_ENABLED
        self._build_ui()
        self.load_recap()

    def _build_ui(self):
        ui.label("Récapitulatif").classes("text-2xl font-bold mb-2")

        self.status = ui.label("En attente").classes("text-sm text-gray-600 mb-3")

        self.table_container = ui.column().classes("w-full")

        ui.button("Rafraîchir", on_click=self.load_recap).classes("mt-3")

    def load_recap(self):
        self.table_container.clear()
        self.status.text = "Chargement..."

        try:
            payload = self._get_payload()

            rows = self._build_rows_from_payload(payload)
            print(rows)
            rows.sort(key=lambda x: x["round"])

            total_rows = self._build_total_rows(payload)

            round_columns = self._get_columns()
            total_columns = self._get_total_columns()

        except Exception as e:
            self.status.text = f"Erreur : {e}"
            return

        if not rows:
            self.status.text = "Aucune donnée"
            ui.label("Aucune donnée à afficher.").classes("text-sm").move(
                self.table_container
            )
            return

        # --- Tableau par round ---
        for round_num, group in groupby(rows, key=lambda x: x["round"]):
            ui.label(f"Round {round_num}").classes("text-h6 mt-4").move(
                self.table_container
            )

            ui.table(
                columns=round_columns,
                rows=list(group),
            ).move(self.table_container)

        # --- Classement général ---
        ui.separator().move(self.table_container)

        ui.label("Classement général").classes("text-h5 mt-6").move(
            self.table_container
        )

        ui.table(
            columns=total_columns,
            rows=total_rows,
        ).move(self.table_container)

        self.status.text = "Chargé"

    def _get_payload(self):
        if self.AUTH_ENABLED:
            return self.api.recap()

        return {
            "round_score": [
                [
                    ("Team A", 1, 200),
                    ("Team B", 1, 200),
                    ("Team C", 1, 200),
                    ("Team D", 1, 200),
                    ("Team A", 2, 400),
                    ("Team B", 2, 400),
                    ("Team C", 2, 400),
                    ("Team D", 2, 400),
                ]
            ],
            "total_score": {
                "Team A": 600,
                "Team B": 600,
                "Team C": 600,
                "Team D": 600,
            },
        }

    @staticmethod
    def _get_columns():
        return [
            {
                "name": "round",
                "label": "Round",
                "field": "round",
                "sortable": True,
            },
            {
                "name": "player",
                "label": "Joueur",
                "field": "player",
            },
            {
                "name": "score",
                "label": "Score",
                "field": "score",
                "sortable": True,
            },
        ]

    @staticmethod
    def _get_total_columns():
        return [
            {"name": "player", "label": "Équipe", "field": "player", "sortable": True},
            {
                "name": "score",
                "label": "Score total",
                "field": "score",
                "sortable": True,
            },
        ]

    @staticmethod
    def _build_rows_from_payload(payload):
        print("Payload:", payload)
        rows = []
        for game in payload["round_score"]:
            player, round_num, score = game
            rows.append(
                {
                    "round": round_num,
                    "player": player,
                    "score": score,
                }
            )
        return rows

    @staticmethod
    def _build_total_rows(payload):
        return [
            {"player": team, "score": total}
            for team, total in payload["total_score"].items()
        ]
