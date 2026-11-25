# Connexion à PostgreSQL et description des tables (ORM SQLAlchemy)

import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import JSON, DateTime, Float, Integer, String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

load_dotenv()  # lit DATABASE_URL dans le fichier .env

engine = create_engine(os.environ["DATABASE_URL"])
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class EmployeTable(Base):
    """Données RH des employés : base d'entraînement du modèle."""

    __tablename__ = "employes"

    id_employee: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    # données utilisées par le modèle
    revenu_mensuel: Mapped[float] = mapped_column(Float)
    poste: Mapped[str] = mapped_column(String(50))
    nombre_experiences_precedentes: Mapped[int]
    annee_experience_totale: Mapped[int]
    annees_dans_l_entreprise: Mapped[int]
    annees_dans_le_poste_actuel: Mapped[int]
    satisfaction_employee_environnement: Mapped[int]
    note_evaluation_precedente: Mapped[int]
    satisfaction_employee_nature_travail: Mapped[int]
    satisfaction_employee_equipe: Mapped[int]
    satisfaction_employee_equilibre_pro_perso: Mapped[int]
    note_evaluation_actuelle: Mapped[int]
    heure_supplementaires: Mapped[str] = mapped_column(String(3))
    augmentation_salaire_precedente: Mapped[float] = mapped_column(Float)
    nombre_participation_pee: Mapped[int]
    nb_formations_suivies: Mapped[int]
    distance_domicile_travail: Mapped[float] = mapped_column(Float)
    niveau_education: Mapped[int]
    domaine_etude: Mapped[str] = mapped_column(String(50))
    frequence_deplacement: Mapped[str] = mapped_column(String(20))
    annees_depuis_la_derniere_promotion: Mapped[int]
    # données du fichier RH non utilisées par le modèle (vides pour les employés ajoutés par l'API)
    age: Mapped[int | None]
    genre: Mapped[str | None] = mapped_column(String(1))
    statut_marital: Mapped[str | None] = mapped_column(String(20))
    departement: Mapped[str | None] = mapped_column(String(50))
    niveau_hierarchique_poste: Mapped[int | None]
    annees_sous_responsable_actuel: Mapped[int | None]
    # cible : 1 = parti, 0 = resté, vide = pas encore connu
    a_quitte_l_entreprise: Mapped[int | None]
    # traçabilité
    source: Mapped[str] = mapped_column(String(10), server_default="fichier")
    date_ajout: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PredictionTable(Base):
    """Journal des appels au modèle : données envoyées et résultat."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date_prediction: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    donnees_entree: Mapped[dict] = mapped_column(JSON)
    probabilite_depart: Mapped[float] = mapped_column(Float)
    risque_depart: Mapped[bool]
    seuil: Mapped[float] = mapped_column(Float)
    version_modele: Mapped[str] = mapped_column(String(20))


def get_session():
    """Ouvre une session pour une requête de l'API, puis la ferme."""
    with SessionLocal() as session:
        yield session


def lire_employes_connus(moteur=engine):
    """Employés de la base dont on sait s'ils sont partis (servent à l'entraînement)."""
    requete = (
        select(EmployeTable)
        .where(EmployeTable.a_quitte_l_entreprise.is_not(None))
        .order_by(EmployeTable.id_employee)
    )
    df = pd.read_sql(requete, moteur)
    return df.drop(columns=["source", "date_ajout"])