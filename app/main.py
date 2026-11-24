# API de prédiction du risque de démission
# Lancement : uv run uvicorn app.main:app --reload

import json
import os

import pandas as pd
from catboost import CatBoostClassifier
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.database import EmployeTable, PredictionTable, get_session
from app.preparation import preparer_features
from app.schemas import Employe, EmployeAjoute, NouvelEmploye, Prediction

load_dotenv()  # lit le fichier .env (clé d'API)

# chargement du modèle une seule fois, au démarrage de l'API
modele = CatBoostClassifier()
modele.load_model("models/model.cbm")
with open("models/model_info.json", encoding="utf-8") as f:
    infos_modele = json.load(f)

app = FastAPI(
    title="TechNova Attrition API",
    description="Prédit le risque de démission d'un employé à partir de ses données RH.",
    version="0.3.0",
)

cle_api_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verifier_cle_api(cle: str | None = Depends(cle_api_header)):
    """Refuse la requête si la clé d'API est absente ou incorrecte."""
    cle_attendue = os.getenv("API_KEY")
    if not cle_attendue or cle != cle_attendue:
        raise HTTPException(status_code=401, detail="Clé d'API absente ou invalide")


@app.get("/health")
def health():
    """Vérifie que l'API fonctionne et indique la version du modèle chargé."""
    return {"statut": "ok", "version_modele": infos_modele["version"]}


@app.post("/predict", response_model=Prediction, dependencies=[Depends(verifier_cle_api)])
def predict(employe: Employe, session: Session = Depends(get_session)):
    """Calcule la probabilité de départ d'un employé et enregistre l'appel dans la base."""
    df = pd.DataFrame([employe.model_dump()])
    X = preparer_features(df, colonnes_modele=infos_modele["colonnes"])
    probabilite = float(modele.predict_proba(X)[0, 1])
    prediction = Prediction(
        probabilite_depart=round(probabilite, 4),
        risque_depart=probabilite >= infos_modele["seuil"],
        seuil=round(infos_modele["seuil"], 4),
        version_modele=infos_modele["version"],
    )

    # traçabilité : données envoyées et résultat du modèle
    session.add(PredictionTable(donnees_entree=employe.model_dump(), **prediction.model_dump()))
    session.commit()
    return prediction


@app.post("/employes", response_model=EmployeAjoute, status_code=201, dependencies=[Depends(verifier_cle_api)])
def ajouter_employe(employe: NouvelEmploye, session: Session = Depends(get_session)):
    """Ajoute un employé dans la base. Le modèle n'est pas réentraîné : l'employé servira au prochain entraînement."""
    if session.get(EmployeTable, employe.id_employee):
        raise HTTPException(status_code=409, detail="Un employé avec cet identifiant existe déjà")

    donnees = employe.model_dump()
    donnees["a_quitte_l_entreprise"] = {"Oui": 1, "Non": 0, None: None}[donnees["a_quitte_l_entreprise"]]
    session.add(EmployeTable(**donnees, source="api"))
    session.commit()
    return EmployeAjoute(
        id_employee=employe.id_employee,
        message="Employé ajouté. Il sera pris en compte au prochain réentraînement du modèle.",
    )