from nicegui import app


def get_token() -> str | None:
    return app.storage.user.get("token")
