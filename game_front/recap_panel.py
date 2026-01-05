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
            recap = payload["recap"]
            recap.sort(key=lambda x: x["round"])
            columns = self._get_columns()

        except Exception as e:
            self.status.text = f"Erreur : {e}"
            return

        if not recap:
            self.status.text = "Aucune donnée"
            ui.label("Aucune donnée à afficher.").classes("text-sm").move(
                self.table_container
            )
            return

        for round_num, rows in groupby(recap, key=lambda x: x["round"]):
            ui.label(f"Round {round_num}").classes("text-h6").move(self.table_container)
            ui.table(
                columns=columns,
                rows=list(rows),
            ).move(self.table_container)

        self.status.text = "Chargé"

    def _get_payload(self):
        if self.AUTH_ENABLED:
            return self.api.recap()

        return {
            "recap": [
                {"round": 1, "player": "bob", "score": 10},
                {"round": 1, "player": "alice", "score": 7},
                {"round": 2, "player": "bob", "score": 18},
            ]
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
