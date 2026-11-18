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
    X = preparer_features(charger_donnees("data"))
    assert X.shape == (1470, 37)
    for colonne in ["id_employee", "a_quitte_l_entreprise", "genre", "age", "statut_marital"]:
        assert colonne not in X.columns


def test_un_seul_employe_aligne_sur_le_modele():
    df = charger_donnees("data")
    colonnes = list(preparer_features(df).columns)
    X_un = preparer_features(df.head(1), colonnes_modele=colonnes)
    assert list(X_un.columns) == colonnes