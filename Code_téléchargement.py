import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

def download_raa():
    url = "https://www.prefecturedepolice.interieur.gouv.fr/votre-prefecture/publications-officielles/recueils-des-actes-administratifs"

    # Lancer Safari
    driver = webdriver.Safari()
    driver.get(url)

    # Attendre que la page charge
    time.sleep(5)

    # Récupérer tous les liens
    elements = driver.find_elements(By.TAG_NAME, "a")

    pdf_links = []

    for el in elements:
        href = el.get_attribute("href")
        if href and ".pdf" in href.lower():
            pdf_links.append(href)

    # Supprimer doublons
    pdf_links = list(set(pdf_links))

    print(f"{len(pdf_links)} PDF trouvés")

    # Créer dossier
    os.makedirs("RAA", exist_ok=True)

    # Télécharger les fichiers
    for link in pdf_links:
        file_name = link.split("/")[-1].split("?")[0]

        print("Téléchargement :", file_name)

        try:
            r = requests.get(link)
            with open(f"RAA/{file_name}", "wb") as f:
                f.write(r.content)
        except Exception as e:
            print("Erreur :", e)

        time.sleep(0.5)

    driver.quit()
    print("Terminé !")

download_raa()
