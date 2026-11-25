# Crée la base PostgreSQL, l'utilisateur de l'API et les tables, puis insère les employés des fichiers CSV
# Lancement : uv run python -m scripts.create_db

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, make_url, text

from app.database import Base, EmployeTable
from app.preparation import charger_donnees

load_dotenv()


def creer_base_et_utilisateur(url_admin, url_api):
    """Crée la base et l'utilisateur de l'API s'ils n'existent pas (connexion administrateur)."""
    moteur = create_engine(url_admin, isolation_level="AUTOCOMMIT")
    with moteur.connect() as conn:
        base_existe = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :nom"), {"nom": url_api.database}
        ).scalar()
        if not base_existe:
            conn.execute(text(f'CREATE DATABASE "{url_api.database}"'))

        utilisateur_existe = conn.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = :nom"), {"nom": url_api.username}
        ).scalar()
        if not utilisateur_existe:
            mot_de_passe = url_api.password.replace("'", "''")
            conn.execute(text(f"CREATE ROLE \"{url_api.username}\" LOGIN PASSWORD '{mot_de_passe}'"))


def donner_droits(moteur, utilisateur):
    """L'API peut seulement lire et ajouter des lignes (ni modifier, ni supprimer)."""
    with moteur.begin() as conn:
        conn.execute(text(f'GRANT SELECT, INSERT ON employes, predictions TO "{utilisateur}"'))
        conn.execute(text(f'GRANT USAGE ON SEQUENCE predictions_id_seq TO "{utilisateur}"'))


def inserer_employes(moteur, dossier="data"):
    """Insère les employés des fichiers CSV si la table est vide ; renvoie le nombre de lignes insérées."""
    with moteur.connect() as conn:
        nb_existants = conn.execute(text("SELECT COUNT(*) FROM employes")).scalar()
    if nb_existants > 0:
        return 0
    df = charger_donnees(dossier)
    df.to_sql(EmployeTable.__tablename__, moteur, if_exists="append", index=False)
    return len(df)


def main():
    url_api = make_url(os.environ["DATABASE_URL"])
    url_admin = make_url(os.environ["ADMIN_DATABASE_URL"])

    creer_base_et_utilisateur(url_admin, url_api)

    # connexion administrateur sur la nouvelle base pour créer les tables
    moteur = create_engine(url_admin.set(database=url_api.database))
    Base.metadata.create_all(moteur)
    donner_droits(moteur, url_api.username)

    nb = inserer_employes(moteur)
    print(f"Base '{url_api.database}' prête : {nb} employés insérés")


if __name__ == "__main__":
    main()