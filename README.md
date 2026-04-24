# game_front

Interface web du jeu en équipes, construite avec [NiceGUI](https://nicegui.io/). Communique avec l'API [`game_back`](https://github.com/Poufoir/game_back).

## Stack technique

- **Python 3.13** + **NiceGUI** — UI web réactive en Python pur
- **Poetry** — gestion des dépendances
- **Docker** — conteneurisation
- **Starlette** — middleware HTTP (garde d'authentification)

## Fonctionnalités

**Interface joueur**
- Authentification (login, premier login avec définition du mot de passe)
- Vue *Règles* — affichage des règles récupérées depuis l'API
- Vue *Tableau principal* — récapitulatif de la partie en cours
- Vue *Actions* — actions disponibles pour le joueur lors de son tour
- Vue *Énigme* — énigme attribuée à l'équipe

**Interface admin** (`/admin`)
- Récapitulatif global : joueurs, actions par round, totaux par équipe
- Gestion des énigmes : validation ou enregistrement d'un échec
- Dons d'argent entre joueurs
- Contrôle des rounds : passage au round suivant, suppression du dernier round

## Structure du projet

```
game_front/
├── app.py                # Point d'entrée principal, pages NiceGUI et middleware
├── game_front/
│   ├── api_client.py     # Client HTTP vers game_back
│   ├── actions_panel.py  # Composant Actions
│   ├── recap_panel.py    # Composant Tableau principal
│   └── utils.py          # Utilitaires (lecture du token, etc.)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── poetry.lock
```

## Lancement en développement

### Prérequis

- Python 3.13
- [Poetry](https://python-poetry.org/docs/#installation)
- [`game_back`](https://github.com/Poufoir/game_back) démarré sur le port `8000`

### Installation

```bash
poetry install
```

### Démarrage

```bash
poetry run python app.py
```

L'interface est accessible sur `http://localhost:8080`.

> Par défaut, `API_BASE` pointe sur `http://127.0.0.1:8000`.  
> Modifiez cette valeur dans `app.py` (ou via variable d'environnement) si le backend tourne sur une autre machine.

## Lancement avec Docker

```bash
docker compose up --build
```

Le service écoute sur le port `8080`.

## Variables d'environnement

| Variable | Description | Défaut |
|---|---|---|
| `API_BASE` | URL du backend `game_back` | `http://127.0.0.1:8000` |
| `STORAGE_SECRET` | Clé secrète pour le stockage de session NiceGUI | *(à définir et à mettre en env)* |

## Désactiver l'authentification (mode dev)

Dans `app.py`, passez `AUTH_ENABLED = False` pour court-circuiter la garde d'authentification et utiliser des données fictives.

## Repo associé

- **Backend** : [`game_back`](https://github.com/Poufoir/game_back) — API FastAPI consommée par cette interface
