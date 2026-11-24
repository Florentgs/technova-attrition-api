# Format des données reçues et renvoyées par l'API (validation avec Pydantic)

from typing import Literal

from pydantic import BaseModel, Field, model_validator

Poste = Literal[
    "Assistant de Direction", "Cadre Commercial", "Consultant", "Directeur Technique", "Manager",
    "Représentant Commercial", "Ressources Humaines", "Senior Manager", "Tech Lead",
]
DomaineEtude = Literal[
    "Autre", "Entrepreneuriat", "Infra & Cloud", "Marketing", "Ressources Humaines", "Transformation Digitale",
]


class Employe(BaseModel):
    """Données d'un employé nécessaires au modèle."""

    revenu_mensuel: float = Field(gt=0)
    poste: Poste
    nombre_experiences_precedentes: int = Field(ge=0)
    annee_experience_totale: int = Field(ge=0, le=60)
    annees_dans_l_entreprise: int = Field(ge=0, le=60)
    annees_dans_le_poste_actuel: int = Field(ge=0, le=60)
    satisfaction_employee_environnement: int = Field(ge=1, le=4)
    note_evaluation_precedente: int = Field(ge=1, le=4)
    satisfaction_employee_nature_travail: int = Field(ge=1, le=4)
    satisfaction_employee_equipe: int = Field(ge=1, le=4)
    satisfaction_employee_equilibre_pro_perso: int = Field(ge=1, le=4)
    note_evaluation_actuelle: int = Field(ge=1, le=4)
    heure_supplementaires: Literal["Oui", "Non"]
    augmentation_salaire_precedente: float = Field(ge=0, le=100, description="En pourcentage")
    nombre_participation_pee: int = Field(ge=0)
    nb_formations_suivies: int = Field(ge=0)
    distance_domicile_travail: float = Field(ge=0)
    niveau_education: int = Field(ge=1, le=5)
    domaine_etude: DomaineEtude
    frequence_deplacement: Literal["Aucun", "Occasionnel", "Fréquent"]
    annees_depuis_la_derniere_promotion: int = Field(ge=0, le=60)

    @model_validator(mode="after")
    def verifier_anciennetes(self):
        """Règles de cohérence entre les différentes durées."""
        if self.annees_dans_l_entreprise > self.annee_experience_totale:
            raise ValueError("annees_dans_l_entreprise ne peut pas dépasser annee_experience_totale")
        if self.annees_dans_le_poste_actuel > self.annees_dans_l_entreprise:
            raise ValueError("annees_dans_le_poste_actuel ne peut pas dépasser annees_dans_l_entreprise")
        return self

    # exemple affiché dans la documentation Swagger
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "revenu_mensuel": 5993, "poste": "Cadre Commercial",
                "nombre_experiences_precedentes": 8, "annee_experience_totale": 8,
                "annees_dans_l_entreprise": 6, "annees_dans_le_poste_actuel": 4,
                "satisfaction_employee_environnement": 2, "note_evaluation_precedente": 3,
                "satisfaction_employee_nature_travail": 4, "satisfaction_employee_equipe": 1,
                "satisfaction_employee_equilibre_pro_perso": 1, "note_evaluation_actuelle": 3,
                "heure_supplementaires": "Oui", "augmentation_salaire_precedente": 11,
                "nombre_participation_pee": 0, "nb_formations_suivies": 0,
                "distance_domicile_travail": 1, "niveau_education": 2,
                "domaine_etude": "Infra & Cloud", "frequence_deplacement": "Occasionnel",
                "annees_depuis_la_derniere_promotion": 0,
            }]
        }
    }


class Prediction(BaseModel):
    """Résultat renvoyé par le modèle."""

    probabilite_depart: float
    risque_depart: bool
    seuil: float
    version_modele: str