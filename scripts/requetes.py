# Exemples de requêtes sur la base et export des prédictions enregistrées
# Lancement : uv run python -m scripts.requetes

import pandas as pd

from app.database import engine

REQUETES = {
    "Employés par origine (fichier RH ou API) et taux de départ": """
        SELECT source, COUNT(*) AS nb_employes,
               ROUND(AVG(a_quitte_l_entreprise) * 100, 1) AS taux_depart_pct
        FROM employes GROUP BY source
    """,
    "Taux de départ par poste": """
        SELECT poste, COUNT(*) AS nb_employes,
               ROUND(AVG(a_quitte_l_entreprise) * 100, 1) AS taux_depart_pct
        FROM employes GROUP BY poste ORDER BY taux_depart_pct DESC
    """,
    "Bilan des prédictions": """
        SELECT version_modele, COUNT(*) AS nb_predictions,
               SUM(CASE WHEN risque_depart THEN 1 ELSE 0 END) AS nb_a_risque,
               ROUND(AVG(probabilite_depart)::numeric, 3) AS probabilite_moyenne
        FROM predictions GROUP BY version_modele
    """,
    "Dernières prédictions": """
        SELECT id, date_prediction, probabilite_depart, risque_depart, version_modele
        FROM predictions ORDER BY date_prediction DESC LIMIT 5
    """,
}

for titre, requete in REQUETES.items():
    print(f"\n{titre}\n{pd.read_sql(requete, engine).to_string(index=False)}")

# export des entrées et sorties du modèle (exemples d'entrées en base)
predictions = pd.read_sql("SELECT * FROM predictions ORDER BY id", engine)
entrees = pd.json_normalize(predictions.pop("donnees_entree").tolist())
pd.concat([predictions, entrees], axis=1).to_csv("exemples/predictions.csv", index=False)
print(f"\n{len(predictions)} prédictions exportées dans exemples/predictions.csv")