import pytest
from fastapi.testclient import TestClient

from app.main import app, infos_modele, modele
from app.preparation import charger_donnees, preparer_features
from app.schemas import Employe

client = TestClient(app)
CLE = "cle-de-test"
EMPLOYE = Employe.model_config["json_schema_extra"]["examples"][0]


@pytest.fixture(autouse=True)
def cle_api(monkeypatch):
    # clé d'API utilisée pendant les tests (indépendante du fichier .env)
    monkeypatch.setenv("API_KEY", CLE)


def predire(donnees, cle=CLE):
    return client.post("/predict", json=donnees, headers={"X-API-Key": cle})


def test_health():
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "ok"


def test_predict_ok():
    reponse = predire(EMPLOYE)
    assert reponse.status_code == 200
    resultat = reponse.json()
    assert 0 <= resultat["probabilite_depart"] <= 1
    assert resultat["risque_depart"] == (resultat["probabilite_depart"] >= infos_modele["seuil"])


def test_predict_meme_resultat_que_le_modele():
    # l'exemple correspond au premier employé du fichier : l'API doit donner
    # la même probabilité que le modèle appliqué directement à ses données
    df = charger_donnees("data")
    X = preparer_features(df.head(1), colonnes_modele=infos_modele["colonnes"])
    attendu = modele.predict_proba(X)[0, 1]
    assert predire(EMPLOYE).json()["probabilite_depart"] == pytest.approx(attendu, abs=1e-4)


def test_predict_sans_cle():
    assert client.post("/predict", json=EMPLOYE).status_code == 401


def test_predict_mauvaise_cle():
    assert predire(EMPLOYE, cle="mauvaise-cle").status_code == 401


@pytest.mark.parametrize("champ, valeur", [
    ("satisfaction_employee_equipe", 5),   # hors de l'échelle 1 à 4
    ("revenu_mensuel", -100),              # revenu négatif
    ("poste", "Astronaute"),               # poste inconnu
    ("heure_supplementaires", "Peut-être"),
])
def test_predict_valeur_invalide(champ, valeur):
    assert predire({**EMPLOYE, champ: valeur}).status_code == 422


def test_predict_champ_manquant():
    donnees = {k: v for k, v in EMPLOYE.items() if k != "poste"}
    assert predire(donnees).status_code == 422


def test_predict_anciennete_incoherente():
    donnees = {**EMPLOYE, "annees_dans_l_entreprise": 10, "annee_experience_totale": 5}
    assert predire(donnees).status_code == 422