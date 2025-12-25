from __future__ import annotations

from nicegui import app, ui
from starlette.responses import RedirectResponse

from game_front.actions_panel import ActionsPanel
from game_front.api_client import ApiClient

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


def get_token() -> str | None:
    return app.storage.user.get("token")


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

        msg = ui.label().classes("text-sm text-red-600")

        def on_login():
            msg.text = ""
            u = (username.value or "").strip()
            p = password.value or ""

            if not u or not p:
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
                set_pending_username(None)
                ui.navigate.to("/")
            elif status == "FIRST_LOGIN":
                set_pending_username(u)
                ui.navigate.to("/set-password")
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
                api.set_password(pending, str(a))
            except Exception as e:
                msg.text = f"Erreur API: {e}"
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
                try:
                    api.logout(token)
                except Exception:
                    pass
                set_token(None)
                ui.navigate.to("/login")

            ui.button("Logout", on_click=do_logout)

    with ui.tabs().classes("w-full") as tabs:
        tab_rules = ui.tab("Règles", icon="info")
        tab_main = ui.tab("Tableau principal", icon="home")
        tab_actions = ui.tab("Actions", icon="gamepad")

    with ui.tab_panels(tabs, value=tab_main).classes("w-full"):
        with ui.tab_panel(tab_rules):
            ui.markdown(RULES_TEXT).classes("prose max-w-none")

        with ui.tab_panel(tab_main):
            ui.label("Récapitulatif").classes("text-2xl font-bold mb-2")

            status = ui.label("En attente").classes("text-sm text-gray-600 mb-3")

            table_container = ui.column().classes("w-full")

            def load_recap():
                table_container.clear()
                status.text = "Chargement..."

                try:
                    if AUTH_ENABLED:
                        payload = api.recap(token)
                    else:
                        payload = {
                            "rows": [
                                {"round": 1, "player": "bob", "score": 10},
                                {"round": 1, "player": "alice", "score": 7},
                                {"round": 2, "player": "bob", "score": 18},
                            ]
                        }

                    rows = payload.get("rows", [])

                except Exception as e:
                    status.text = f"Erreur : {e}"
                    return

                if not rows:
                    status.text = "Aucune donnée"
                    ui.label("Aucune donnée à afficher.").classes("text-sm").move(
                        table_container
                    )
                    return

                ui.table(rows=rows).classes("w-full").move(table_container)
                status.text = "Chargé"

            ui.button("Rafraîchir", on_click=load_recap).classes("mt-3")
            load_recap()

        with ui.tab_panel(tab_actions):
            ActionsPanel(api)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host="0.0.0.0", port=8080, storage_secret="change-me-please")
