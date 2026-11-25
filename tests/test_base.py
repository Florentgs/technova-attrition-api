import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select

from app.database import Base, EmployeTable, PredictionTable, SessionLocal, lire_employes_connus
from app.main import app
from app.preparation import charger_donnees
from app.schemas import NouvelEmploye
from scripts.create_db import inserer_employes

client = TestClient(app)
CLE = "cle-de-test"
NOUVEL_EMPLOYE = NouvelEmploye.model_config["json_schema_extra"]["examples"][0]


@pytest.fixture(autouse=True)
def cle_api(monkeypatch):
    monkeypatch.setenv("API_KEY", CLE)


def ajouter(donnees, cle=CLE):
    return client.post("/employes", json=donnees, headers={"X-API-Key": cle})


def test_predict_enregistre_entree_et_sortie():
    donnees = {k: v for k, v in NOUVEL_EMPLOYE.items() if k not in ("id_employee", "a_quitte_l_entreprise")}
    with SessionLocal() as session:
        nb_avant = session.scalar(select(func.count()).select_from(PredictionTable))

    reponse = client.post("/predict", json=donnees, headers={"X-API-Key": CLE})

    with SessionLocal() as session:
        nb_apres = session.scalar(select(func.count()).select_from(PredictionTable))
        derniere = session.scalars(select(PredictionTable).order_by(PredictionTable.id.desc())).first()
    assert nb_apres == nb_avant + 1
    assert derniere.donnees_entree == donnees
    assert derniere.probabilite_depart == reponse.json()["probabilite_depart"]


def test_ajouter_employe():
    reponse = ajouter({**NOUVEL_EMPLOYE, "id_employee": 5001})
    assert reponse.status_code == 201
    with SessionLocal() as session:
        employe = session.get(EmployeTable, 5001)
    assert employe.source == "api"
    assert employe.a_quitte_l_entreprise is None


def test_ajouter_employe_avec_issue_connue():
    assert ajouter({**NOUVEL_EMPLOYE, "id_employee": 5002, "a_quitte_l_entreprise": "Oui"}).status_code == 201
    with SessionLocal() as session:
        assert session.get(EmployeTable, 5002).a_quitte_l_entreprise == 1


def test_ajouter_employe_deja_existant():
    ajouter({**NOUVEL_EMPLOYE, "id_employee": 5003})
    assert ajouter({**NOUVEL_EMPLOYE, "id_employee": 5003}).status_code == 409


def test_ajouter_employe_sans_cle():
    assert ajouter({**NOUVEL_EMPLOYE, "id_employee": 5004}, cle="mauvaise-cle").status_code == 401


@pytest.mark.parametrize("champ, valeur", [
    ("id_employee", -1),
    ("a_quitte_l_entreprise", "Peut-être"),
    ("satisfaction_employee_equipe", 7),
])
def test_ajouter_employe_invalide(champ, valeur):
    assert ajouter({**NOUVEL_EMPLOYE, champ: valeur}).status_code == 422


def test_insertion_et_lecture_pour_entrainement(tmp_path):
    # base séparée : insertion des fichiers CSV puis lecture des employés dont l'issue est connue
    moteur = create_engine(f"sqlite:///{tmp_path / 'base.db'}")
    Base.metadata.create_all(moteur)
    nb_employes_csv = len(charger_donnees("data"))
    assert inserer_employes(moteur) == nb_employes_csv
    assert inserer_employes(moteur) == 0  # pas de doublon si on relance le script

    with moteur.begin() as conn:
        conn.execute(EmployeTable.__table__.insert().values({**NOUVEL_EMPLOYE, "id_employee": 9999}))

    df = lire_employes_connus(moteur)
    assert len(df) == nb_employes_csv  # l'employé sans issue connue est exclu
    assert "source" not in df.columns