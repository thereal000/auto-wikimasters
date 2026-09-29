```python
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime

import browser_cookie3
import requests


API_URL = "https://www.wiki-masters.com/api/packs/open"

INITIAL_PACKS = 10
POLL_INTERVAL = 10 * 60
REQUEST_TIMEOUT = (10, 30)

PACK_DELAY = 5
MAX_RETRIES = 3
AUTH_COOLDOWN = 10 * 60
RATE_LIMIT_FALLBACK = 60


RED = "\033[91m"
RESET = "\033[0m"


@dataclass
class Result:
    status: str
    remaining: int | None = None


class WikiMaster:
    def __init__(self) -> None:
        self.session = self._build_session()
        self.auth_blocked_until: float | None = None

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()

        cookies = browser_cookie3.chrome(
            domain_name="www.wiki-masters.com"
        )

        session.cookies.update(cookies)

        session.headers.update({
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/153.0.0.0 Safari/537.36"
            ),
        })

        return session

    def _request(self) -> Result:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.post(
                    API_URL,
                    timeout=REQUEST_TIMEOUT,
                )

            except requests.Timeout:
                if attempt == MAX_RETRIES:
                    print("La connexion a mis trop de temps.")
                    return Result("temporary")

                delay = min(5 * attempt, 20)
                print(f"Ça a pris trop de temps, nouvel essai dans {delay}s.")
                time.sleep(delay)
                continue

            except requests.ConnectionError:
                if attempt == MAX_RETRIES:
                    print("Connexion impossible pour le moment.")
                    return Result("temporary")

                delay = min(5 * attempt, 30)
                print(f"Connexion perdue, nouvel essai dans {delay}s.")
                time.sleep(delay)
                continue

            except requests.RequestException:
                print("Un problème est survenu pendant la requête.")
                return Result("temporary")

            status = response.status_code

            if status == 200:
                try:
                    payload = response.json()
                except ValueError:
                    print("La réponse reçue n'est pas valide.")
                    return Result("temporary")

                remaining = payload.get("packs_remaining")

                try:
                    remaining = int(remaining)
                except (TypeError, ValueError):
                    remaining = None

                return Result("success", remaining)

            if status in (401, 403):
                self.auth_blocked_until = (
                    time.monotonic() + AUTH_COOLDOWN
                )
                return Result("auth")

            if status == 429:
                retry_after = response.headers.get("Retry-After")

                try:
                    delay = max(float(retry_after), 1)
                except (TypeError, ValueError):
                    delay = RATE_LIMIT_FALLBACK

                print(f"Un peu trop vite, je réessaie dans {delay:.0f}s.")
                time.sleep(delay)
                continue

            if 500 <= status < 600:
                if attempt == MAX_RETRIES:
                    print("Le serveur ne répond pas correctement.")
                    return Result("temporary")

                delay = min(2 ** attempt, 30)
                print(f"Le serveur a eu un souci, nouvel essai dans {delay}s.")
                time.sleep(delay)
                continue

            print(f"Requête refusée ({status}).")
            return Result("fatal")

        return Result("temporary")

    def open_pack(self) -> Result:
        if (
            self.auth_blocked_until is not None
            and time.monotonic() < self.auth_blocked_until
        ):
            return Result("auth")

        return self._request()


def wait(seconds: float) -> None:
    deadline = time.monotonic() + seconds

    while True:
        remaining = deadline - time.monotonic()

        if remaining <= 0:
            return

        time.sleep(min(remaining, 30))


def timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def main() -> None:
    print(f"{RED}wikimaster{RESET}")
    print("by @cry4me")
    print()

    try:
        client = WikiMaster()
    except Exception:
        print("Impossible de récupérer la session Chrome.")
        return

    print(f"[{timestamp()}] C'est parti.")

    for index in range(INITIAL_PACKS):
        result = client.open_pack()

        if result.status == "success":
            if result.remaining is None:
                print(f"[{timestamp()}] Pack ouvert.")
            else:
                print(
                    f"[{timestamp()}] Pack ouvert "
                    f"({result.remaining} restant)"
                )

                if result.remaining <= 0:
                    print("Plus aucun pack disponible.")
                    break

        elif result.status == "auth":
            print("La session n'est plus reconnue.")
            print("Je laisse tourner et je réessaierai plus tard.")
            break

        elif result.status == "temporary":
            print("Petit problème de connexion, j'arrête pour l'instant.")
            break

        else:
            print("La requête n'est pas passée.")
            break

        if index + 1 < INITIAL_PACKS:
            wait(PACK_DELAY)

    print("Je vérifierai toutes les 10 minutes.")

    while True:
        wait(POLL_INTERVAL)

        result = client.open_pack()

        if result.status == "success":
            if result.remaining is None:
                print(f"[{timestamp()}] Pack ouvert.")
            else:
                print(
                    f"[{timestamp()}] Pack ouvert "
                    f"({result.remaining} restant)"
                )

        elif result.status == "auth":
            print(
                f"[{timestamp()}] Session refusée, "
                "je réessaierai au prochain passage."
            )

        elif result.status == "temporary":
            print(
                f"[{timestamp()}] Problème temporaire, "
                "je réessaierai au prochain passage."
            )

        else:
            print(
                f"[{timestamp()}] La requête n'est pas passée."
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nArrêt.")
```
