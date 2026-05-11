"""
Pipeline de normalisation RAA-NORM.

Ce package contient les 8 etapes du pipeline de normalisation
des Recueils des Actes Administratifs. 

Ordre d'execution :
    1. encoding    - Correction encodage + mojibake
    2. unicode     - Normalisation NFC + homoglyphes
    3. ocr_repair  - Reparation erreurs OCR
    4. typography  - Typographie francaise
    5. structure   - Uniformisation articles/alineas
    6. casing      - Harmonisation capitalisation
    6.2 sections   - Délimitation des différentes parties des RAA
    7. final       - Nettoyage final + validation
"""
