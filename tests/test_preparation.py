import json

import pandas as pd

from app.preparation import charger_donnees, preparer_features


def test_jointure_une_ligne_par_employe():
    df = charger_donnees("data")
    nb_employes_sirh = len(pd.read_csv("data/extrait_sirh.csv"))
    assert len(df) == nb_employes_sirh
    assert df["id_employee"].is_unique
    assert df.isna().sum().sum() == 0


def test_cible_en_0_1():
    df = charger_donnees("data")
    assert set(df["a_quitte_l_entreprise"]) == {0, 1}


def test_features_sans_variables_sensibles():
    df = charger_donnees("data")
    X = preparer_features(df)

    # autant de lignes que d'employés, aucune valeur manquante, que des nombres
    assert len(X) == len(df)
    assert X.isna().sum().sum() == 0
    assert X.select_dtypes(exclude="number").empty

    # mêmes colonnes, dans le même ordre, que celles du modèle enregistré
    with open("models/model_info.json", encoding="utf-8") as f:
        colonnes_modele = json.load(f)["colonnes"]
    assert list(X.columns) == colonnes_modele

    # ni identifiant, ni cible, ni variable sensible (y compris colonnes encodées)
    interdites = ["id_employee", "a_quitte_l_entreprise", "genre", "age", "statut_marital"]
    for colonne in X.columns:
        assert not colonne.startswith(tuple(interdites))


def test_un_seul_employe_aligne_sur_le_modele():
    df = charger_donnees("data")
    colonnes = list(preparer_features(df).columns)
    X_un = preparer_features(df.head(1), colonnes_modele=colonnes)
    assert list(X_un.columns) == colonnes