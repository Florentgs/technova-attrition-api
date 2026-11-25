# Entraîne le modèle CatBoost du projet d'attrition et l'enregistre dans models/
# Lancement : uv run python -m scripts.train          (à partir des fichiers CSV)
#             uv run python -m scripts.train --base   (à partir de la base PostgreSQL)

import json
import sys
from datetime import date

import numpy as np
from catboost import CatBoostClassifier
from sklearn.metrics import average_precision_score, confusion_matrix, precision_recall_curve, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split

from app.preparation import CIBLE, charger_donnees, preparer_features

RANDOM_STATE = 42
VERSION_MODELE = "1.0.0"

# hyperparamètres trouvés par RandomizedSearchCV lors de la modélisation
PARAMETRES = {
    "depth": 2,
    "iterations": 761,
    "learning_rate": 0.02544166090938368,
    "l2_leaf_reg": 9.51975448269268,
    "random_strength": 2.600340105889054,
}


def creer_modele():
    return CatBoostClassifier(auto_class_weights="Balanced", random_state=RANDOM_STATE,
                              verbose=0, allow_writing_files=False, **PARAMETRES)


def main():
    if "--base" in sys.argv:
        from app.database import lire_employes_connus
        df = lire_employes_connus()
    else:
        df = charger_donnees("data")
    X = preparer_features(df)
    y = df[CIBLE]
    print("X :", X.shape, "- départs :", y.sum())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    # seuil : maximum du F2 sur les prédictions hors échantillon du jeu d'apprentissage
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    proba_oof = cross_val_predict(creer_modele(), X_train, y_train, cv=cv, method="predict_proba")[:, 1]
    precisions, rappels, seuils = precision_recall_curve(y_train, proba_oof)
    f2 = 5 * precisions[:-1] * rappels[:-1] / np.maximum(4 * precisions[:-1] + rappels[:-1], 1e-12)
    seuil = float(seuils[np.argmax(f2)])
    print(f"Seuil retenu : {seuil:.2f}")

    # modèle entraîné sur le jeu d'apprentissage puis évalué une seule fois sur le test
    modele = creer_modele()
    modele.fit(X_train, y_train)
    proba_test = modele.predict_proba(X_test)[:, 1]
    y_pred = (proba_test >= seuil).astype(int)

    metriques_test = {
        "precision": round(precision_score(y_test, y_pred), 2),
        "rappel": round(recall_score(y_test, y_pred), 2),
        "average_precision": round(average_precision_score(y_test, proba_test), 2),
        "matrice_confusion": confusion_matrix(y_test, y_pred).tolist(),
    }
    print("Test :", metriques_test)

    modele.save_model("models/model.cbm")
    infos = {
        "version": VERSION_MODELE,
        "date_entrainement": str(date.today()),
        "seuil": seuil,
        "colonnes": list(X.columns),
        "parametres": PARAMETRES,
        "metriques_test": metriques_test,
    }
    with open("models/model_info.json", "w", encoding="utf-8") as f:
        json.dump(infos, f, ensure_ascii=False, indent=2)
    print("Modèle enregistré dans models/")


if __name__ == "__main__":
    main()