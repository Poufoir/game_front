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
        self.status.text = "Chargement..."

        self.table_container.clear()

        try:
            payload = self._get_payload()
            full_total = payload.get("total", 0)
            teams = payload.get("round_score", [])

            if not teams:
                self.status.text = "Aucune donnée"
                return

            rounds = sorted(
                {r for team in teams for r in team["rounds"].keys()}, key=int
            )

            with self.table_container:
                with ui.table(
                    columns=[
                        {"name": "team", "label": "Équipe", "field": "team"},
                        *[
                            {"name": f"r{r}", "label": f"Round {r}", "field": f"r{r}"}
                            for r in rounds
                        ],
                    ],
                    rows=[],
                ).classes(
                    "w-full q-table--horizontal-separator q-table--vertical-separator"
                ) as table:
                    rows = []

                    for team in teams:
                        row = {"team": team["team"]}

                        last_value = 0

                        for r in rounds:
                            value = team["rounds"].get(r, last_value)
                            row[f"r{r}"] = value

                        rows.append(row)

                    table.rows = rows
                with ui.row().classes("justify-end mt-2"):
                    ui.label(
                        f"Total général pour les tribus principales: {full_total}"
                    ).classes("text-lg font-semibold")

            self.status.text = "OK"

        except Exception as e:
            self.status.text = f"Erreur: {e}"

    def _get_payload(self):
        if self.AUTH_ENABLED:
            return self.api.recap()

        return {
            "round_score": [
                {"team": "Team A", "rounds": {"1": 0, "2": 300, "3": 600}},
                {"team": "Team B", "rounds": {"1": 0, "2": 300, "3": 600}},
                {"team": "Team C", "rounds": {"1": 0, "2": 300, "3": 600}},
                {"team": "Team D", "rounds": {"1": 0, "2": 300, "3": 600}},
            ]
        }
