# Préparation des données : reprend le nettoyage et les variables du notebook d'analyse

import numpy as np
import pandas as pd

CIBLE = "a_quitte_l_entreprise"

SATISFACTIONS = [
    "satisfaction_employee_environnement",
    "satisfaction_employee_nature_travail",
    "satisfaction_employee_equipe",
    "satisfaction_employee_equilibre_pro_perso",
]

# Colonnes retirées : identifiant, redondantes et sensibles (genre, âge, statut marital)
COLONNES_A_RETIRER = [
    "id_employee", "departement", "niveau_hierarchique_poste",
    "annees_dans_le_poste_actuel", "annees_sous_responsable_actuel",
    "genre", "age", "statut_marital",
]


def charger_donnees(dossier="data"):
    """Charge, nettoie et joint les trois fichiers (une ligne par employé)."""
    sirh = pd.read_csv(f"{dossier}/extrait_sirh.csv")
    evaluations = pd.read_csv(f"{dossier}/extrait_eval.csv")
    sondage = pd.read_csv(f"{dossier}/extrait_sondage.csv")

    # colonnes constantes
    sirh = sirh.drop(columns=["nombre_heures_travailless"])
    sondage = sondage.drop(columns=["nombre_employee_sous_responsabilite", "ayant_enfants"])

    # fautes de frappe
    evaluations = evaluations.rename(columns={"augementation_salaire_precedente": "augmentation_salaire_precedente"})
    sondage = sondage.rename(columns={"annes_sous_responsable_actuel": "annees_sous_responsable_actuel"})
    sondage["domaine_etude"] = sondage["domaine_etude"].replace({"Entrepreunariat": "Entrepreneuriat"})
    sondage["frequence_deplacement"] = sondage["frequence_deplacement"].replace({"Frequent": "Fréquent"})

    # "11 %" -> 11.0 et cible en 0/1
    evaluations["augmentation_salaire_precedente"] = (
        evaluations["augmentation_salaire_precedente"].str.replace("%", "").str.strip().astype(float)
    )
    sondage[CIBLE] = sondage[CIBLE].map({"Oui": 1, "Non": 0})

    # clés de jointure : "E_12" -> 12 et code_sondage -> id_employee
    evaluations["id_employee"] = evaluations["eval_number"].str.split("_").str[1].astype(int)
    evaluations = evaluations.drop(columns=["eval_number"])
    sondage = sondage.rename(columns={"code_sondage": "id_employee"})

    df = sirh.merge(evaluations, on="id_employee", validate="one_to_one")
    df = df.merge(sondage, on="id_employee", validate="one_to_one")
    return df


def ratio(numerateur, denominateur, valeur_si_zero):
    """Divise deux colonnes ; renvoie valeur_si_zero quand le dénominateur vaut 0."""
    return (numerateur / denominateur.replace(0, np.nan)).fillna(valeur_si_zero)


def preparer_features(df, colonnes_modele=None):
    """Crée les variables, les encode et renvoie X.

    colonnes_modele : liste des colonnes vues à l'entraînement, pour aligner
    les données d'un seul employé sur celles du modèle (prédiction).
    """
    df = df.copy()

    # variables créées
    df["part_carriere_entreprise"] = ratio(df["annees_dans_l_entreprise"], df["annee_experience_totale"], 1)
    df["part_anciennete_poste_actuel"] = ratio(df["annees_dans_le_poste_actuel"], df["annees_dans_l_entreprise"], 1)
    df["nb_satisfactions_faibles"] = (df[SATISFACTIONS] == 1).sum(axis=1)
    df["duree_moyenne_par_employeur"] = df["annee_experience_totale"] / (df["nombre_experiences_precedentes"] + 1)

    df = df.drop(columns=[c for c in COLONNES_A_RETIRER + [CIBLE] if c in df.columns])

    # encodage
    df["heure_supplementaires"] = (df["heure_supplementaires"] == "Oui").astype(int)
    df["frequence_deplacement"] = df["frequence_deplacement"].map({"Aucun": 0, "Occasionnel": 1, "Fréquent": 2})
    df = pd.get_dummies(df, columns=["poste", "domaine_etude"], dtype=int)

    if colonnes_modele is not None:
        df = df.reindex(columns=colonnes_modele, fill_value=0)
    return df