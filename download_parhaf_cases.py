"""
Telecharge le dataset HealthDataHub/PARHAF depuis Hugging Face et le convertit
en data/parhaf_cases.parquet, le fichier source consomme par generate_data.py.

Dataset source : https://huggingface.co/datasets/HealthDataHub/PARHAF
"""

from pathlib import Path

import pandas as pd
from datasets import load_dataset

DATA_DIR = Path(__file__).parent / "data"
PARHAF_CASES_PATH = DATA_DIR / "parhaf_cases.parquet"


def extract_age(scenario):
    age = scenario["age"]
    # L'age suggere n'est fiable qu'en annees ("mois" concerne des nourrissons
    # marginaux dans le dataset source) ; on retombe sur 0 sinon.
    return age["value"] if age["unit"] == "ans" else 0


def extract_duree_sejour(length_of_stay):
    if length_of_stay is None:
        return None
    if length_of_stay["unit"] != "jours" or length_of_stay["value"] == 0:
        return None
    return length_of_stay["value"]


def build_case(row):
    scenario = row["suggested_scenario"]
    documents = row["documents"]

    return {
        "case_id": row["id"],
        "specialty": row["specialty"],
        "name": scenario["name"],
        "age": extract_age(scenario),
        "sex": scenario["sex"],
        "discharge_mode": scenario["discharge_mode"],
        "duree_sejour": extract_duree_sejour(row["structured_abstract"]["length_of_stay"]),
        "documents": [
            {"type": t, "header": h, "text": txt}
            for t, h, txt in zip(documents["type"], documents["header"], documents["text"])
        ],
    }


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dataset = load_dataset("HealthDataHub/PARHAF")["train"]

    cases = [
        build_case(row)
        for row in dataset
        if "CRH" in row["documents"]["type"]
    ]

    df = pd.DataFrame(cases)
    df.to_parquet(PARHAF_CASES_PATH, index=False)
    print(f"parhaf_cases : {len(df):>5} lignes (cas avec au moins un CRH)")
    print(f"Fichier ecrit dans {PARHAF_CASES_PATH}")


if __name__ == "__main__":
    main()
