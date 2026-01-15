from __future__ import annotations

import asyncio

from nicegui import app, ui
from starlette.responses import RedirectResponse

from game_front.actions_panel import ActionsPanel
from game_front.api_client import ApiClient
from game_front.recap_panel import RecapView
from game_front.utils import get_token

API_BASE = "http://127.0.0.1:8000"  # mets IP du backend si autre machine
api = ApiClient(API_BASE)

AUTH_ENABLED = True

RULES_TEXT = """
### Règles du jeu (récap)
- Objectif : ...
- Tour de jeu : ...
- Points : ...
- Conditions de victoire : ...
"""


def set_token(token: str | None) -> None:
    if token:
        app.storage.user["token"] = token
    else:
        app.storage.user.pop("token", None)


def set_pending_username(username: str | None) -> None:
    if username:
        app.storage.user["pending_username"] = username
    else:
        app.storage.user.pop("pending_username", None)


def get_pending_username() -> str | None:
    return app.storage.user.get("pending_username")


@app.middleware("http")
async def guard(request, call_next):
    if not AUTH_ENABLED:
        return await call_next(request)

    path = request.url.path
    if path.startswith("/_nicegui"):
        return await call_next(request)

    public = {"/login", "/set-password", "/favicon.ico"}
    if path not in public and not get_token():
        return RedirectResponse(url="/login", status_code=302)

    return await call_next(request)


@ui.page("/login")
def login_page() -> None:
    ui.query("body").classes("bg-gray-50")

    with ui.card().classes("w-full max-w-md mx-auto mt-24 p-6"):
        ui.label("Connexion").classes("text-2xl font-bold")

        username = (
            ui.input("Nom d'utilisateur")
            .props("autocomplete=username")
            .classes("w-full")
        )
        password = (
            ui.input("Mot de passe", password=True, password_toggle_button=True)
            .props("autocomplete=current-password")
            .classes("w-full")
        )
        password.set_visibility(False)

        msg = ui.label().classes("text-sm text-red-600")

        def on_login():
            msg.text = ""
            u = (username.value or "").strip()
            p = password.value or ""

            if not u:
                msg.text = "Veuillez saisir un nom d'utilisateur et un mot de passe."
                return

            try:
                res = api.login(u, p)
            except Exception as e:
                msg.text = f"Erreur API: {e}"
                return

            status = res.get("status")
            print(f"login status: {status}")
            if status == "OK":
                set_token(res["token"])
                set_pending_username(u)
                if u == "admin":
                    ui.navigate.to("/admin")
                else:
                    ui.navigate.to("/")
            elif status == "FIRST_LOGIN":
                set_pending_username(u)
                ui.navigate.to("/set-password")
            elif status == "PASSWORD_REQUIRED":
                set_pending_username(u)
                password.set_visibility(True)
            elif status == "UNKNOWN_USER":
                msg.text = "Utilisateur inconnu."
            else:
                msg.text = "Identifiants invalides."

        ui.button("Se connecter", on_click=on_login).classes("w-full mt-2")


@ui.page("/set-password")
def set_password_page() -> None:
    ui.query("body").classes("bg-gray-50")

    pending = get_pending_username()
    if not pending:
        ui.navigate.to("/login")
        return

    with ui.card().classes("w-full max-w-md mx-auto mt-24 p-6"):
        ui.label("Définir votre mot de passe").classes("text-2xl font-bold")
        ui.label(f"Utilisateur: {pending}").classes("text-sm text-gray-600")

        pw1 = ui.input(
            "Nouveau mot de passe", password=True, password_toggle_button=True
        ).classes("w-full")
        pw2 = ui.input(
            "Confirmer le mot de passe", password=True, password_toggle_button=True
        ).classes("w-full")
        msg = ui.label().classes("text-sm text-red-600")

        def on_set():
            msg.text = ""
            a = pw1.value or ""
            b = pw2.value or ""

            if len(a) < 8:
                msg.text = "Mot de passe trop court (min 8 caractères)."
                return
            if a != b:
                msg.text = "Les mots de passe ne correspondent pas."
                return

            try:
                answer = api.set_password(pending, str(a))
                print(f"set_password answer: {answer.get('status')}")
            except Exception as e:
                msg.text = f"Erreur API: {e}"
                print(f"Error setting password: {e}")
                return

            set_pending_username(None)
            ui.notify("Mot de passe défini. Connectez-vous.")
            ui.navigate.to("/login")

        ui.button("Enregistrer", on_click=on_set).classes("w-full mt-2")
        ui.button(
            "Annuler",
            on_click=lambda: (set_pending_username(None), ui.navigate.to("/login")),
        ).props("flat").classes("w-full")


@ui.page("/")
def main_page() -> None:
    if AUTH_ENABLED:
        token = get_token()
        if not token:
            ui.navigate.to("/login")
            return
        try:
            me = api.me(token)
            username = me["username"]
        except Exception:
            set_token(None)
            ui.navigate.to("/login")
            return
    else:
        token = None
        username = "DEV_MODE"

    with ui.header().classes("items-center justify-between"):
        ui.label(f"Game UI — utilisateur: {username}").classes("text-lg font-semibold")

        if AUTH_ENABLED:

            def do_logout():
                set_token(None)
                ui.navigate.to("/login")

            ui.button("Logout", on_click=do_logout)

    with ui.tabs().classes("w-full") as tabs:
        tab_rules = ui.tab("Règles", icon="info")
        tab_main = ui.tab("Tableau principal", icon="home")
        tab_actions = ui.tab("Actions", icon="gamepad")

    actions_panel = None
    panels = ui.tab_panels(tabs, value=tab_main).classes("w-full")

    with panels:
        with ui.tab_panel(tab_rules):
            RULES_TEXT = api.get_rules()
            ui.markdown(RULES_TEXT).classes("prose max-w-none")

        with ui.tab_panel(tab_main):
            RecapView(api, AUTH_ENABLED=AUTH_ENABLED)

        with ui.tab_panel(tab_actions):
            actions_panel = ActionsPanel(api)

    def on_panel_change(e):
        if e.value == "Actions" and actions_panel is not None:
            asyncio.create_task(actions_panel.refresh())

    panels.on_value_change(on_panel_change)


@ui.page("/admin")
def admin_page():
    token = get_token()
    if not token or get_pending_username() != "admin":
        ui.navigate.to("/login")
        return

    data = api.admin_recap(token)

    current_round = data["round"]
    players = data["players"]
    teams = data["money"]

    ui.query("body").classes("bg-gray-100")

    with ui.column().classes("max-w-7xl mx-auto p-6 gap-4"):
        ui.label(f"🎮 ADMIN – Tour actuel : {current_round}").classes(
            "text-3xl font-bold mb-4"
        )
        with ui.tabs().classes("w-full") as tabs:
            recap_tab = ui.tab("📋 Récap")
            donation_tab = ui.tab("💝 Don")

        with ui.tab_panels(tabs, value=recap_tab).classes("w-full"):
            with ui.tab_panel(recap_tab):
                with ui.row().classes("w-full gap-6 flex-nowrap"):
                    with ui.column().classes("w-2/3"):
                        ui.label("📋 Joueurs").classes("text-2xl font-bold")
                        for p in players:
                            with ui.card().classes("p-4 w-full"):
                                ui.label(f"👤 {p['username']} — {p['team']}").classes(
                                    "font-bold"
                                )

                                with ui.column().classes("pl-4 mt-2 gap-1"):
                                    for r in p["rounds"]:
                                        ui.label(
                                            f"Round {r['round']} | {r['mode']} | {r['action']} | 💰 {r['money']} €"
                                        ).classes("text-sm")
                    with ui.column().classes("w-1/3"):
                        ui.label("💰 Totaux par équipe").classes(
                            "text-2xl font-bold mt-6"
                        )

                        for team in teams:
                            with ui.card().classes("p-4"):
                                ui.label(f"🏷 {team['team']}").classes("font-bold")
                                ui.label(f"Total: {team['total']} €")

                                with ui.row().classes("gap-4 text-sm mt-2"):
                                    for round_id, amount in team["rounds"].items():
                                        ui.label(f"R{round_id}: {amount} €")

            with ui.tab_panel(donation_tab):
                with ui.card().classes("max-w-md mx-auto p-6 gap-4"):
                    ui.label("💝 Faire un don").classes("text-xl font-bold")
                    player_names = api.get_player_names()
                    player_input = ui.select(
                        player_names,
                        label="Joueur",
                        with_input=True,
                    ).classes("w-full")

                    amount_input = ui.number(
                        label="Montant",
                        min=0,
                        step=5,
                        format="%.0f",
                    ).classes("w-full")

                    result = ui.label()

                    def send_donation():
                        player = player_input.value
                        amount = int(amount_input.value or 0)

                        if not player or amount <= 0:
                            result.text = "❌ Veuillez remplir tous les champs"
                            result.classes("text-red-600")
                            return

                        api.donate(
                            token=get_token(),
                            username=player,
                            amount=amount,
                        )

                        result.text = f"✅ {amount}€ donné par {player}"
                        result.classes("text-green-600")

                        amount_input.value = None

                    ui.button("💝 Valider le don", on_click=send_donation).classes(
                        "bg-pink-600 text-white w-full"
                    )
                with ui.row().classes("mt-6 justify-between"):
                    ui.button(
                        "➕ Lancer le round suivant",
                        on_click=lambda: api.admin_next_round(token=get_token()),
                    ).classes("bg-green-600 text-white")

                    ui.button(
                        "⏪ Supprimer le dernier round",
                        on_click=lambda: api.admin_delete_last_round(token=get_token()),
                    ).classes("bg-red-600 text-white")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host="0.0.0.0", port=8080, storage_secret="change-me-please")
