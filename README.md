# TechNova Attrition API

Mise en production d'un modèle de machine learning qui prédit le risque de démission des employés de TechNova Partners.

Le modèle est un CatBoost entraîné sur les données RH de 1 470 employés (SIRH, évaluations annuelles et sondage interne). Sur le jeu de test, il détecte 79 % des départs avec un seuil de 0,36.

## Installation

Il faut avoir Git et uv installés.

    git clone https://github.com/Florentgs/technova-attrition-api.git
    cd technova-attrition-api
    uv sync

Sans uv : `pip install -r requirements.txt`.

## Entraîner le modèle

    uv run python -m scripts.train

Le modèle est enregistré dans `models/model.cbm`, et ses informations (version, seuil, colonnes, résultats sur le test) dans `models/model_info.json`.

## Lancer les tests

    uv run pytest