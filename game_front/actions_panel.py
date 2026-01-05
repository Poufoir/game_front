from nicegui import ui

from game_front.api_client import ApiClient

MODE_COLORS = {
    "Récolte": "green",
    "Embuscade": "red",
    "Contre-Attaque": "blue",
}

ACTION_COLOR = "purple-6"


class ActionsPanel:
    def __init__(self, api: ApiClient):
        self.api = api

        self.current_mode = None
        self.current_action = None

        self.mode_buttons = {}
        self.action_buttons = {}

        self.build()

    def build(self):
        ui.label("Actions").classes("text-2xl font-bold mb-4")

        self._build_mode_block()
        self._build_action_block()

    def _build_mode_block(self):
        with ui.card().classes("border-2 border-blue-500 w-full mb-4"):
            ui.label("Mode").classes("text-lg font-semibold text-blue-600 mb-2")

            with ui.row():
                for mode, color in MODE_COLORS.items():
                    btn = ui.button(
                        mode, on_click=lambda m=mode: self.set_mode(m)
                    ).props(f"color={color}")

                    self.mode_buttons[mode] = btn

    def _build_action_block(self):
        with ui.card().classes("border-2 border-yellow-500 w-full"):
            ui.label("Action principale").classes(
                "text-lg font-semibold text-yellow-600 mb-2"
            )

            with ui.row():
                for action in ["Pilier", "Cailloux"]:
                    btn = ui.button(
                        action, on_click=lambda a=action: self.set_action(a)
                    ).props(f"color={ACTION_COLOR}")

                    self.action_buttons[action] = btn

    def set_mode(self, mode: str):
        self.current_mode = mode
        self.api.set_mode(mode)
        self._update_mode_styles()

    def set_action(self, action: str):
        self.current_action = action
        self.api.set_action(action)
        self._update_action_styles()

    def _update_mode_styles(self):
        for name, btn in self.mode_buttons.items():
            color = MODE_COLORS[name]

            if name == self.current_mode:
                btn.props(remove="outline")
                btn.props(f"color={color} unelevated icon=check")
            else:
                btn.props(remove="unelevated text-color=white")
                btn.props(f"color={color} outline icon=none")

    def _update_action_styles(self):
        for name, btn in self.action_buttons.items():
            if name == self.current_action:
                btn.props(remove="outline")
                btn.props(f"color={ACTION_COLOR} unelevated icon=check")
            else:
                btn.props(remove="unelevated text-color=white")
                btn.props(f"color={ACTION_COLOR} outline icon=none")
