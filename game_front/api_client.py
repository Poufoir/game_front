from __future__ import annotations

from typing import Union

import requests


class ApiClient:
    def __init__(self, base_url: str, timeout_s: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def _get(self, path: str, params: dict) -> Union[dict, str]:
        r = requests.get(
            f"{self.base_url}{path}", params=params, timeout=self.timeout_s
        )
        if r.status_code >= 400:
            try:
                detail = r.json().get("detail", r.text)
            except Exception:
                detail = r.text
            raise RuntimeError(detail)
        return r.json()

    def _post(self, path: str, json: dict) -> dict:
        r = requests.post(f"{self.base_url}{path}", json=json, timeout=self.timeout_s)
        if r.status_code >= 400:
            try:
                detail = r.json().get("detail", r.text)
            except Exception:
                detail = r.text
            raise RuntimeError(detail)
        return r.json()

    def login(self, username: str, password: str) -> dict:
        return self._post("/auth/login", {"username": username, "password": password})

    def set_password(self, username: str, new_password: str) -> dict:
        return self._post(
            "/auth/set-password", {"username": username, "password": new_password}
        )

    def me(self, token: str) -> dict:
        return self._get("/users/me", {"token": token})

    def recap(self) -> dict:
        return self._get("/recap", {})

    def logout(self, token: str) -> dict:
        return self._post("/auth/logout", {"token": token})

    def set_mode(self, token: str, mode: str) -> dict:
        return self._post("/users/set-mode", {"token": token, "mode": mode})

    def set_action(self, token: str, action: str) -> dict:
        return self._post("/users/set-action", {"token": token, "action": action})

    def get_rules(self) -> str:
        return self._get("/rules", {})
