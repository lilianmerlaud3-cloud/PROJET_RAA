# RAA Cleaner 

## Présentation

RAA Cleaner est un outil Python permettant le nettoyage, la normalisation et la segmentation automatique des Recueils des Actes Administratifs (RAA).

L’application traite des fichiers texte issus d’OCR ou de PDF administratifs afin :
- de corriger les erreurs d’encodage et de typographie ;
- de restructurer le contenu ;
- de détecter automatiquement les arrêtés ;
- d’exporter chaque arrêté dans un fichier indépendant.

Le projet a initialement été conçu comme une application web, puis transformé en outil exécutable en ligne de commande afin de faciliter les traitements batch et l’automatisation.

---

## Fonctionnalités principales

- Nettoyage OCR et Unicode ;
- Normalisation de la structure des documents ;
- Détection automatique des arrêtés administratifs ;
- Extraction et export des arrêtés ;
- Conservation du contexte administratif du RAA (en-tête et sommaire) dans chaque fichier exporté ;
- Pipeline modulaire de traitement.

---

## Structure du projet

```text
RAA_v2/
│
├── main.py
├── pipeline.py
├── config.py
│
├── steps/
│   ├── __init__.py
│   ├── step_01_encoding.py
│   ├── step_02_unicode.py
│   ├── step_03_ocr_repair.py
│   ├── step_04_typography.py
│   ├── step_05_structure.py
│   ├── step_06_casing.py
│   ├── step_06_2_sections.py
│   ├── step_07_final.py
│
├── utils/
│   ├── __init__.py
│   ├── detector.py
│   ├── diff_engine.py
│   ├── validators.py
│   └── segmentation_arrete.py
│   └── __pycache__/
│
└── raa_avant/
```

---

## Exécution

L'exécution se fait directement depuis la ligne de commande : `python main.py`

Étape 1 : On inscrit dans le code le dossier contenant les RAA à nettoyer et normaliser.
Étape 2 : On tape la commande depuis la ligne de commande.
Étape 3 : Le code crée automatiquement un nouveau dossier dans le dossier contenant les RAA et y place tous les arrêtés normalisés et nettoyés.


---

## Auteurs

ALLIOUA Maïlisse
NEVE-LESBATS Clémence











