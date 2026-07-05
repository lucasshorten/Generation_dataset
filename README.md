# Generation Dataset PARHAF

Generation d'un jeu de donnees synthetique de type entrepot de donnees de sante
(patients, sejours, mouvements, documents cliniques) a partir du dataset public
[HealthDataHub/PARHAF](https://huggingface.co/datasets/HealthDataHub/PARHAF).

Les cas PARHAF (comptes-rendus medicaux fictifs, redigers par des internes)
servent de source de contenu clinique realiste ; ce depot les recombine en un
schema relationnel simple (patient / sejour / mouvement / document / biologie /
medicament / constante) avec des identifiants sequentiels generes localement.
Le nom des patients present dans le dataset source n'est pas repris dans les
fichiers generes.

Le dossier `data/` (fichiers `.parquet` generes) n'est pas versionne — suivez
les etapes ci-dessous pour le reconstruire localement.

## Prerequis

- Python 3.10+
- Un acces internet pour telecharger le dataset depuis Hugging Face

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # Linux/macOS

pip install -r requirements.txt
```

## Reproduire les fichiers `data/*.parquet`

### 1. Telecharger et convertir le dataset source PARHAF

```bash
python download_parhaf_cases.py
```

Ce script :
- telecharge le dataset `HealthDataHub/PARHAF` (split `train`, ~4250 cas) via
  la librairie `datasets` (mis en cache dans `~/.cache/huggingface`) ;
- ne conserve que les cas comportant au moins un document de type `CRH`
  (compte-rendu d'hospitalisation), soit ~3560 cas ;
- aplatit chaque cas en un enregistrement `case_id, specialty, name, age,
  sex, discharge_mode, duree_sejour, documents` ;
- ecrit le resultat dans `data/parhaf_cases.parquet`.

### 2. Generer le jeu de donnees synthetique

```bash
python generate_data.py
```

A partir d'un echantillon de 100 cas PARHAF (graine fixe `SEED = 42` pour la
reproductibilite), ce script genere sept fichiers coherents entre eux dans
`data/` :

- `patient.parquet` — un patient par cas (`id_patient`, `age`, `sexe`, `date_deces` eventuelle)
- `sejour.parquet` — un sejour hospitalier par cas (dates d'entree/sortie, UF)
- `mouvement.parquet` — mouvements intra-sejour (une UF par sejour dans cette version)
- `document.parquet` — documents cliniques (CRH/CRC/CRO) rattaches au sejour, au format HTML
- `biologie.parquet` — resultats de biologie rattaches au sejour (`id_biologie`, `id_patient`,
  `id_sejour`, `uf`, `date_prelevement`, `valeur_numerique` ou `valeur_texte` selon le type de
  resultat, `unite` du resultat numerique)
- `medicament.parquet` — administrations medicamenteuses rattachees au sejour (`id_medicament`,
  `id_patient`, `id_sejour`, `date_administration`, `quantite_administree`, `unite`, `ucd`, `atc`,
  `voie_administration`, `conditionnelle` (administration systematique ou si besoin), `commentaire`)
- `constante.parquet` — constantes vitales rattachees au sejour, au format long (`id_constante`,
  `id_patient`, `id_sejour`, `type_constante`, `date`, `valeur`, `unite`) ; types couverts : poids,
  taille, temperature, frequence cardiaque, frequence respiratoire, saturation en oxygene, pression
  arterielle systolique/diastolique

### 3. (Optionnel) Explorer les donnees generees

Le notebook `revue.ipynb` fournit un apercu (head, stats, valeurs manquantes)
de chaque fichier `data/*.parquet` :

```bash
jupyter notebook revue.ipynb
```

## Structure du depot

```
generate_data.py           # genere data/{patient,sejour,mouvement,document,biologie,medicament,constante}.parquet
download_parhaf_cases.py   # genere data/parhaf_cases.parquet depuis Hugging Face
revue.ipynb                # revue exploratoire des fichiers generes
requirements.txt
data/                      # non versionne — voir "Reproduire les fichiers"
```
