import html
import random
from datetime import timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

SEED = 42
N_PATIENTS = 100
DATA_DIR = Path(__file__).parent / "data"
PARHAF_CASES_PATH = DATA_DIR / "parhaf_cases.parquet"

# Un cas PARHAF (projet PARTAGES / HealthDataHub) = un patient = un sejour :
# age, sexe, mode de sortie, duree de sejour et documents proviennent tous
# du meme cas pour rester coherents entre eux.
DOCUMENT_TYPE_LABELS = {
    "CRH": "Compte-rendu d'hospitalisation",
    "CRC": "Compte-rendu de consultation",
    "CRO": "Compte-rendu operatoire",
}

BIOLOGY_TEXT_VALUES = ["positif", "negatif", "normal", "anormal", "non contributif"]

# UCD illustratifs (non officiels) associes a un code ATC reel, pour un
# echantillon de medicaments courants.
MEDICATIONS = [
    {"ucd": "3400893940692", "atc": "N02BE01", "unite": "mg", "dose": (500, 1000)},
    {"ucd": "3400935861654", "atc": "M01AE01", "unite": "mg", "dose": (200, 400)},
    {"ucd": "3400892014319", "atc": "J01CA04", "unite": "mg", "dose": (500, 1000)},
    {"ucd": "3400930093625", "atc": "A02BC01", "unite": "mg", "dose": (20, 40)},
    {"ucd": "3400921959219", "atc": "B01AC06", "unite": "mg", "dose": (75, 300)},
    {"ucd": "3400937246430", "atc": "C09AA02", "unite": "mg", "dose": (5, 20)},
    {"ucd": "3400935928562", "atc": "A10BA02", "unite": "mg", "dose": (500, 1000)},
    {"ucd": "3400892449517", "atc": "N05BA01", "unite": "mg", "dose": (2, 10)},
    {"ucd": "3400930096770", "atc": "C10AA05", "unite": "mg", "dose": (10, 80)},
    {"ucd": "3400927699023", "atc": "N02AA01", "unite": "mg", "dose": (5, 20)},
]

random.seed(SEED)
Faker.seed(SEED)
fake = Faker("fr_FR")


def load_parhaf_cases():
    return pd.read_parquet(PARHAF_CASES_PATH)


def build_uf_by_specialty(specialties):
    return {
        specialty: f"{1000 + 10 * i:04d}"
        for i, specialty in enumerate(sorted(specialties))
    }


def make_html_document(header, text):
    paragraphs = "".join(
        f"<p>{html.escape(p)}</p>" for p in text.split("\n\n") if p.strip()
    )
    return f"<h1>{html.escape(header)}</h1>{paragraphs}"


def random_datetime_during_stay(date_entree, date_sortie):
    total_seconds = int((date_sortie - date_entree).total_seconds())
    if total_seconds <= 0:
        return date_entree
    return date_entree + timedelta(seconds=random.randint(0, total_seconds))


def generate():
    cases = load_parhaf_cases().sample(n=N_PATIENTS, random_state=SEED).to_dict("records")
    uf_by_specialty = build_uf_by_specialty(c["specialty"] for c in cases)

    patients, sejours, mouvements, documents = [], [], [], []
    biologies, medicaments = [], []
    document_counter = 1
    biologie_counter = 1
    medicament_counter = 1

    for i, case in enumerate(cases, start=1):
        id_patient = f"PAT{i:06d}"
        id_sejour = f"SEJ{i:06d}"
        uf = uf_by_specialty[case["specialty"]]

        date_entree = fake.date_time_between(start_date="-3y", end_date="-6M")
        duree = int(case["duree_sejour"]) if pd.notna(case["duree_sejour"]) else random.randint(1, 30)
        date_sortie = date_entree + timedelta(days=duree)

        mouvements.append({
            "id_mouvement": f"MVT{i:06d}",
            "id_sejour": id_sejour,
            "uf": uf,
            "date_entree": date_entree,
            "date_sortie": date_sortie,
        })

        sejours.append({
            "id_sejour": id_sejour,
            "id_patient": id_patient,
            "date_entree": date_entree,
            "date_sortie": date_sortie,
            "uf_entree": uf,
            "uf_sortie": uf,
            "specialite": case["specialty"],
        })

        for doc in case["documents"]:
            type_document = DOCUMENT_TYPE_LABELS.get(doc["type"])
            if type_document is None:
                continue
            documents.append({
                "id_entrepot": f"DOC{document_counter:06d}",
                "id_patient": id_patient,
                "id_sejour": id_sejour,
                "titre": f"{type_document} - {date_sortie.date()}",
                "type_document": type_document,
                "texte_affichage": make_html_document(doc["header"], doc["text"]),
            })
            document_counter += 1

        for _ in range(random.randint(2, 8)):
            is_numeric = random.random() < 0.75
            # Plage numerique arbitraire : aucune valeur de reference clinique
            # n'est associee (pas de nom d'analyte dans ce schema simplifie).
            biologies.append({
                "id_biologie": f"BIO{biologie_counter:06d}",
                "id_patient": id_patient,
                "id_sejour": id_sejour,
                "uf": uf,
                "date_prelevement": random_datetime_during_stay(date_entree, date_sortie),
                "valeur_numerique": round(random.uniform(0.1, 200), 2) if is_numeric else None,
                "valeur_texte": None if is_numeric else random.choice(BIOLOGY_TEXT_VALUES),
            })
            biologie_counter += 1

        for _ in range(random.randint(1, 5)):
            medication = random.choice(MEDICATIONS)
            medicaments.append({
                "id_medicament": f"MED{medicament_counter:06d}",
                "id_patient": id_patient,
                "id_sejour": id_sejour,
                "date_administration": random_datetime_during_stay(date_entree, date_sortie),
                "quantite_administree": random.randint(*medication["dose"]),
                "unite": medication["unite"],
                "ucd": medication["ucd"],
                "atc": medication["atc"],
            })
            medicament_counter += 1

        date_deces = (
            date_sortie + timedelta(days=random.randint(0, 5))
            if case["discharge_mode"] == "décès"
            else None
        )

        patients.append({
            "id_patient": id_patient,
            "age": case["age"],
            "sexe": case["sex"],
            "date_deces": date_deces,
        })

    return (
        pd.DataFrame(patients),
        pd.DataFrame(sejours),
        pd.DataFrame(mouvements),
        pd.DataFrame(documents),
        pd.DataFrame(biologies),
        pd.DataFrame(medicaments),
    )


def validate_coherence(df_sejour, df_mouvement):
    mvt_by_sejour = {
        id_sejour: group.sort_values("date_entree")
        for id_sejour, group in df_mouvement.groupby("id_sejour")
    }
    for sejour_row in df_sejour.itertuples():
        mvts = mvt_by_sejour[sejour_row.id_sejour]
        assert mvts["date_entree"].iloc[0] == sejour_row.date_entree, sejour_row.id_sejour
        assert mvts["date_sortie"].iloc[-1] == sejour_row.date_sortie, sejour_row.id_sejour
        entrees = mvts["date_entree"].to_numpy()[1:]
        sorties = mvts["date_sortie"].to_numpy()[:-1]
        assert (entrees == sorties).all(), sejour_row.id_sejour


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df_patient, df_sejour, df_mouvement, df_document, df_biologie, df_medicament = generate()
    df_patient["date_deces"] = pd.to_datetime(df_patient["date_deces"])
    validate_coherence(df_sejour, df_mouvement)

    df_patient.to_parquet(DATA_DIR / "patient.parquet", index=False)
    df_sejour.to_parquet(DATA_DIR / "sejour.parquet", index=False)
    df_mouvement.to_parquet(DATA_DIR / "mouvement.parquet", index=False)
    df_document.to_parquet(DATA_DIR / "document.parquet", index=False)
    df_biologie.to_parquet(DATA_DIR / "biologie.parquet", index=False)
    df_medicament.to_parquet(DATA_DIR / "medicament.parquet", index=False)

    print(f"patient    : {len(df_patient):>5} lignes")
    print(f"sejour     : {len(df_sejour):>5} lignes")
    print(f"mouvement  : {len(df_mouvement):>5} lignes")
    print(f"document   : {len(df_document):>5} lignes")
    print(f"biologie   : {len(df_biologie):>5} lignes")
    print(f"medicament : {len(df_medicament):>5} lignes")
    print(f"Fichiers ecrits dans {DATA_DIR}")


if __name__ == "__main__":
    main()
