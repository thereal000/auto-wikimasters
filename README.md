# wikimasters

Petit script Python pour ouvrir automatiquement les packs de WikiMasters.

Le script utilise une session Chrome déjà ouverte. Il ne contourne ni ne désactive la protection anti-bot du site.

## Prérequis

* Python 3.10+
* Google Chrome
* Une session Wiki-Masters déjà ouverte dans Chrome

## Installation

```bash
git clone https://github.com/cry4me/wikimaster.git
cd wikimaster
pip install -r requirements.txt
```

## Utilisation

Connecte-toi à Wiki-Masters dans Chrome, puis lance :

```bash
python main.py
```

Le script ouvre jusqu'à 10 packs au démarrage, puis fait une tentative toutes les 10 minutes.

## Dépendances

* `requests`
* `browser-cookie3`
