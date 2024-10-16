import json
import os
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from utils import send_email_with_attachment, export_to_excell
from webdriver_manager.chrome import ChromeDriverManager


def parse_capital_retail(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    # service = Service(_path)  # Remplacez par le chemin de votre chromedriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    deals_data = []
    try:
        driver.get(url)
        time.sleep(5)

        # Sélectionner les éléments contenant les informations souhaitées
        properties = driver.find_elements(By.CSS_SELECTOR, 'div.cInner-Container.doubleView')
        print("nb de props", len(properties))

        # Extraire les informations de chaque propriété
        for prop in properties:
            # Prix on ne ramasse que Sale et sale et lease
            price = prop.find_element(By.CSS_SELECTOR, 'div.cInner-Contents div.cInner-Price').text
            if price.startswith('For Lease'):
                continue
            # Type de propriété
            property_type = prop.find_element(By.CSS_SELECTOR, 'div.cInner-Contents div.cInner-Category').text

            # Adresse
            address = prop.find_element(By.CSS_SELECTOR, 'div.cInner-Contents div.cInner-Label').text

            # Disponibilité
            availability = prop.find_element(By.CSS_SELECTOR, 'div.cInner-Contents div.cInner-Avail').text

            # Surface en pieds carrés
            building_sqft = prop.find_element(By.CSS_SELECTOR, 'div.cInner-Contents div.cInner-Sqm').text

            # URL du détail de la propriété
            detail_url = prop.find_element(By.CSS_SELECTOR, 'a.propLink').get_attribute('href')

            # Affichage des résultats
            print(f"Type: {property_type}")
            print(f"Price: {price}")
            print(f"Address: {address}")
            print(f"Availability: {availability}")
            print(f"Building Sq Ft: {building_sqft}")
            print(f"Detail URL: {detail_url}")
            print("=" * 20)

            deal_data = {
                "Address": address,
                "Zip_code": "view address",
                "Detail URL and contact page": detail_url,
                "Price": price,
                "Built sqft or acres": building_sqft,
                "Property Type": property_type,
                "Latitude": "N/A",
                "Longitude": "N/A"
            }
            deals_data.append(deal_data)

    except Exception as e:
        print(e)

    finally:
        driver.quit()
        return deals_data


if __name__ == "__main__":
    start_time = time.time()
    load_dotenv()
    site_url = "https://www.capitalretailproperties.com/properties/"

    data = parse_capital_retail(site_url)

    nb_properties = len(data)
    filename, file_path, current_date = export_to_excell(data, "Capital Retail Properties")
    end_time = time.time()
    duration = (end_time - start_time)
    print("durée totale en secondes: ", int(duration), "pour: ", nb_properties)
    body = f"Le scraping du broker Capital Retail Properties au {current_date}, \nconcerne {nb_properties} terrains ou bâtiments à vendre.\nMerci de les consulter en fichier joint"

    sender_email = os.getenv("sender_email")
    sender_password = os.getenv("sender_password")
    recipient_email = os.getenv("recipient")
    subject = "[Capital Retail Properties: Excel en pièce jointe]"
    cc_email = os.getenv("cc_email")

    send_email_with_attachment(sender_email, sender_password, recipient_email, subject, body, file_path, cc_email)
